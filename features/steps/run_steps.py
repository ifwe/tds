import os
import time
import shlex
import sys
import subprocess

import tds
import tds.utils as utils
import tds.utils.processes as processes
import tds.scripts.tds_prog as prog
from behave import given, when, then

TDS_SCRIPT = tds.scripts.tds_prog.__file__
TRACEBACK_TEXT = 'Traceback (most recent call last)'

@when(u'I run "{command}"')
def when_i_run_command(context, command):
    context.execute_steps('''
        When I start to run "%s"
        And the command finishes
    ''' % command)

@when(u'I start to run "{command}"')
def when_i_start_to_run(context, command):
    env = os.environ.copy()
    env['PYTHONPATH'] = context.PROJECT_ROOT
    env['BEHAVE_WORK_DIR'] = context.WORK_DIR
    proc = None

    cmd_parts = shlex.split(command.encode('utf8'))

    if getattr(context, 'coverage_enabled', False):
        cmd_executable = [
            "coverage", "run",
            "--append",
            "--branch",
            '--rcfile="%s"' % os.path.join(context.PROJECT_ROOT, 'coverage.rc'),
            '--source=%s' % ','.join(['tds']),
        ]
    else:
        cmd_executable = [
            sys.executable
        ]

    cmd_parts = (
        cmd_executable +
        [TDS_SCRIPT] +
        getattr(context, 'extra_run_args', []) +
        cmd_parts
    )

    try:
        proc = processes.start_process(
            cmd_parts,
            cwd=context.PROJECT_ROOT,
            env=env
        )
    except subprocess.CalledProcessError as proc:
        pass

    context.process = proc

@when(u'I wait {number} seconds')
def when_i_wait_seconds(context, number):
    time.sleep(int(number))

@when(u'the command finishes')
def when_the_command_finishes(context):
    context.process = processes.wait_for_process(
        context.process,
        expect_return_code=None
    )

    if 'wip' not in context.tags:
        context.execute_steps(u'Then the output has no errors')


def output_checker(context, check):
    stdout = context.process.stdout.strip()
    stderr = context.process.stderr.strip()

    assert check(stdout, stderr), (stdout, stderr)

@then(u'the output has "{text}"')
def then_the_output_has_text(context, text):
    output_checker(context, lambda out, err: text in out or text in err)


@then(u'the output has no errors')
def then_the_output_has_no_errors(context):
    output_checker(
        context,
        lambda out, err: not (TRACEBACK_TEXT in err or TRACEBACK_TEXT in out)
    )


@then(u'the output is "{text}"')
def then_the_output_is_text(context, text):
    output_checker(context, lambda out, err: text == out or text == err)


@then(u'the output is empty')
def then_the_output_is_empty(context):
    output_checker(context, lambda out, *_a: len(out) == 0)


@then(u'it took at least {seconds} seconds')
def then_it_took_at_least_seconds(context, seconds):
    assert context.process.duration >= float(seconds)

@then(u'the test fails')
def then_the_test_fails(context):
    assert False, 'step triggered failure'
