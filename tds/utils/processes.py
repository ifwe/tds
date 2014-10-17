"""Utilities to run subprocesses."""

import time
import shlex
import subprocess
import collections


def run(cmd, expect_return_code=0, shell=False, **kwds):
    """Wrapper to run external command"""

    proc = start_process(cmd, shell=shell, **kwds)
    return wait_for_process(proc, expect_return_code=expect_return_code, **kwds)


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
        exc = subprocess.CalledProcessError(1, args)
        exc.stderr = 'Error using Popen: %s' % e
        exc.stdout = None
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
        exc = subprocess.CalledProcessError(proc.returncode, proc.cmd)
        exc.stderr = stderr
        exc.stdout = stdout
        exc.duration = duration
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
