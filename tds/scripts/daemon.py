# Copyright 2023 The Meet Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Base class for TDS Daemons. Handle common zookeeper operations, etc.
'''

import logging
import signal
import socket
import traceback
import sys

from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import CancelledError, ConnectionClosedError, LockTimeout
from kazoo.retry import KazooRetry

log = logging.getLogger('tds.scripts.daemon')


class TDSDaemon(object):
    '''
    Base class for a TDS daemon.
    '''

    def __init__(self, app):
        self.app = app
        self._should_stop = False
        self.has_lock = False
        self.lock = None
        self.lock_is_stale = False
        # These optional callbacks may be overriden by a child class.
        self.end_callback = None
        self.loop_callback = None

    def cancel_lock(self):
        """
        Tell kazoo to cancel any pending lock. Any lock acquisition in progress
        will raise a CancelledError exception the next time kazoo is allowed to
        run.
        """
        if self.lock is not None:
            log.debug("Cancelling pending ZooKeeper lock (if any).")
            # This is idempotent; no need to set self.lock to None.
            self.lock.cancel()
            log.debug("Cancelled pending ZooKeeper lock (if any).")

    def create_zoo(self, zoo_config):
        """
        Create a new zookeeper object as self.zoo; return a zookeeper lock.
        """
        hostname = socket.gethostname()

        # Set up our own KazooRetry classes in order to override default
        # parameters.
        command_retry = KazooRetry(
            # Old default is 3600; modern default is 60; we should be ok at 10.
            max_delay=10,
            # callback
            interrupt=self.should_stop,
        )
        connection_retry = KazooRetry(
            max_delay=10,
            # Retry forever (unless interrupted).
            max_tries=-1,
            interrupt=self.should_stop,
        )
        kzlog = log.getChild('kazoo')
        # debug is too verbose
        kzlog.setLevel(logging.INFO)
        self.zoo = KazooClient(
            hosts=','.join(zoo_config),
            # This sets the timeout on connections (and reconnections).
            timeout=3,
            connection_retry=connection_retry,
            command_retry=command_retry,
            logger=kzlog,
        )

        def state_listener(state):
            """
            Handle callbacks run when kazoo's internal state changes.
            """
            prefix = "Detected new Kazoo state: "
            if not self.should_stop():
                if state == KazooState.CONNECTED:
                    log.info(prefix + "Connected to ZooKeeper.")
                else:
                    if state == KazooState.SUSPENDED:
                        # Note: kazoo itself logs that the connection is
                        # "lost", before setting its own internal state to
                        # SUSPENDED.
                        log.warning(prefix + "ZooKeeper connection suspended.")
                    elif state == KazooState.LOST:
                        log.warning(prefix + "ZooKeeper connection lost.")
                    else:
                        log.error("Unrecognized ZooKeeper state: %s" % (state))

                    # Trust in KazooClient to reconnect as needed, but don't
                    # trust the state of the lock. The lock may or may not
                    # still exist. We need to release the lock (if it exists),
                    # but we can't do that here, since calling back into kazoo
                    # code from within the kazoo-called callback causes
                    # trouble.
                    log.debug("Marking zookeeper lock as stale.")
                    self.lock_is_stale = True

        self.zoo.add_listener(state_listener)
        self.zoo.start()
        return self.zoo.Lock(self.zookeeper_path, hostname)

    def configure(self):
        """
        Child classes may override this for daemon-specific configuration.
        """
        pass

    def lock_run(self, func, *args, **kwargs):
        """
        Run the specified function, with the specified arguments, under a
        zookeeper lock. This will block until the lock is acquired or
        shutdown is initiated. Once done, the lock is not released, such that
        it may be re-used by subsequent runs. Lock release is handled:
        1. During shutdown.
        2. In the code within the loop below, if zookeeper connection trouble
           indicates that we can't trust whether or not we have a lock.
        """
        if not self.has_lock:
            # Trigger a lock removal below, just to be sure.
            self.lock_is_stale = True

        while (self.lock_is_stale or not self.has_lock) and not self.should_stop():
            # self.lock_is_stale may become True due to a kazoo callback.
            if self.lock_is_stale:
                # If a lock _does_ exist, then attempting to get a lock will
                # block, so we need to be certain there is none.
                # This call is idempotent.
                log.debug("Clearing out any existing ZooKeeper lock.")
                self.release_lock()
                self.lock_is_stale = False
                log.debug("Waiting to acquire ZooKeeper lock.")
            try:
                # If no timeout is specified here, then kazoo will block on a
                # threading wait, which blocks the signal handler (at least on
                # python < 3.3).
                # If any timeout is specified, then kazoo will run an internal
                # check-sleep loop which does not block the signal handler. Do
                # not specify too low a timeout or else there will be a high
                # turnover of ephemeral zookeeper nodes, leading to overflow of
                # the (apparently) signed 32-bit int counter on the parent
                # node.
                # A timeout of 60 should give us a zookeer node lifetime of
                # 4085 years.
                self.has_lock = self.lock.acquire(timeout=60)
            except CancelledError:
                log.debug("ZooKeeper lock acquisition cancelled")
            except LockTimeout:
                pass

            if self.has_lock:
                log.debug("Acquired ZooKeeper lock")

        # Once execution reaches this point, then we either got a lock, so run
        # the supplied function, or we are in shutdown (see loop conditions
        # above).
        if self.has_lock:
            func(*args, **kwargs)
        elif self.should_stop():
            log.debug("Aborted acquiring ZooKeeper lock due to shutdown")

    def main(self):
        """
        Read configuration file and get relevant information; if zookeeper is
        in use, wait for a zookeper lock. Once operating, run callbacks.
        """
        if hasattr(self.app, 'initialize'):
            self.app.initialize()

        self.configure()
        zookeeper_config = self.app.config.get('zookeeper', None)

        if zookeeper_config is not None:
            self.lock = self.create_zoo(zookeeper_config)
            self.zk_run = self.lock_run
        else:
            self.zk_run = lambda f, *a, **k: f(*a, **k)

        while not self.should_stop():
            try:
                self.zk_run(self.run_callback)
            except ConnectionClosedError:
                # Only raise error when we are not stopping. If we're stopping
                # anyway, we don't care if kazoo is having trouble.
                if not self.should_stop():
                    raise

            if self.loop_callback:
                self.loop_callback()

        if self.end_callback:
            self.end_callback()

        if self.zoo is not None:
            if self.lock is not None:
                self.release_lock()

            self.zoo.stop()
            self.zoo.close()

        log.info("Stopped.")

    def release_lock(self):
        """
        Release any acquired lock; this needs to be able to communicate with
        zookeeper.
        """
        if self.has_lock:
            log.debug("Releasing ZooKeeper lock.")
            # Tell kazoo that it has a lock in order to force kazoo to attempt
            # to remove the corresponding node, even if kazoo doesn't think
            # there is one.
            self.lock.is_acquired = True
            self.lock.release()
            log.debug("Released ZooKeeper lock.")
            self.has_lock = False

    def run(self):
        """A wrapper for the main process to ensure any unhandled
           exceptions are logged before the daemon exits.
        """
        try:
            self.main()
        except Exception as exc:
            msg = "Unhandled exception: %r.  Daemon exiting." % exc
            msg += '\n' + traceback.format_exc()
            log.error(msg)
            sys.exit(1)

    def should_stop(self):
        return self._should_stop

    def shutdown_handler(self, signum, frame):
        """
        Shut down the daemon.
        """
        # Python < 3.5 doesn't have an easy number-->name translation.
        log.fatal('Received signal %d. Beginning shutdown...' % (signum))
        # Reset handler so that repeated signals cause immediate shutdown.
        signal.signal(signum, signal.SIG_DFL)

        self._should_stop = True
        if self.lock is not None:
            # Cancel any pending lock acquisition. This will cause kazoo to
            # raise a CancelledError, which we catch.
            self.cancel_lock()
