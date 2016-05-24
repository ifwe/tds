# Copyright 2016 Ifwe Inc.
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

"""Utilities to run subprocesses."""

import collections
import shlex
import subprocess
import time

from tds.exceptions import RunProcessError


def run(cmd, expect_return_code=0, shell=False, **kwds):
    """Wrapper to run external command"""

    proc = start_process(cmd, shell=shell, **kwds)
    return wait_for_process(proc, expect_return_code=expect_return_code,
                            **kwds)


def start_process(cmd, shell=False, **kwds):
    """
    Start a subprocess.

    Return a token-like object that can be used in a call to
    `wait_for_process` to end the process and get the results.
    """
    if isinstance(cmd, basestring):
        args = shlex.split(cmd.replace('\\', '\\\\'))
    else:
        args = cmd

    args = map(str, args)

    try:
        start = time.time()
        proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=shell, **kwds)
        proc.cmd = args
        proc.start_time = start
    except OSError as e:
        exc = RunProcessError(1, args, stderr='Error using Popen: %s' % e)
        raise exc

    return proc


def wait_for_process(proc, expect_return_code=0, **_kwds):
    """
    Finalize a process token and return information about the ended process.

    This is a blocking call if the subprocess has not yet finished.

    process.duration is not strictly correct -- if the process ended
    before the call to this function, the duration will be inflated.
    """
    stdout, stderr = proc.communicate()
    end = time.time()
    duration = end - proc.start_time

    if not (expect_return_code is None or
            expect_return_code == proc.returncode):
        exc = RunProcessError(proc.returncode, proc.cmd, stdout=stdout,
                              stderr=stderr, duration=duration)
        raise exc

    process = collections.namedtuple(
        'Process',
        ['cmd', 'stdout', 'stderr', 'returncode', 'duration']
    )

    return process(
        cmd=proc.cmd,
        stdout=stdout,
        stderr=stderr,
        returncode=proc.returncode,
        duration=duration
    )
