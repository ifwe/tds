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

"""Execution management for feature tests"""

import os
import time
import shlex
import sys
import subprocess

import tds
import tds.exceptions
import tds.scripts.tds_prog
import tds.scripts.unvalidated_deploy_check
import tds.utils.processes as processes
import tds.apps.repo_updater

from behave import given, when, then

TDS_SCRIPT = tds.scripts.tds_prog.__file__
REPO_UPDATE_SCRIPT = tds.apps.repo_updater.__file__
DEPLOY_DAEMON_SCRIPT = tds.apps.installer.__file__
UNVALIDATED_CHECK_SCRIPT = tds.scripts.unvalidated_deploy_check.__file__
TRACEBACK_TEXT = 'Traceback (most recent call last)'


@when(u'I run "{command}"')
def when_i_run_command(context, command):
    context.execute_steps('''
        When I start to run "%s"
        And the command finishes
    ''' % command)


@when(u'I start to run "{command}"')
def when_i_start_to_run(context, command):
    helpers_path = os.path.join(context.PROJECT_ROOT, 'features', 'helpers', 'bin')
    helpers_lib_path = os.path.join(context.PROJECT_ROOT, 'features', 'helpers', 'lib')
    env = os.environ.copy()
    env['PATH'] = os.pathsep.join(filter(None, [helpers_path, env.get('PATH', '')]))
    env['PYTHONPATH'] = os.pathsep.join([helpers_lib_path, context.PROJECT_ROOT])
    env['BEHAVE_WORK_DIR'] = context.WORK_DIR
    proc = None

    cmd_parts = shlex.split(command.encode('utf8'))

    if getattr(context, 'coverage_enabled', False):
        cmd_executable = context.coverage_cmd('run') + [
            "--append",
            "--branch",
            '--source=%s' % ','.join(['tds']),
        ]
    else:
        cmd_executable = [
            sys.executable
        ]

    if cmd_parts[0] == 'check':
        cmd_parts = (
            cmd_executable +
            [UNVALIDATED_CHECK_SCRIPT] +
            getattr(context, 'extra_run_args', [])
        )
    elif cmd_parts[0] == "daemon":
        cmd_parts = (
            cmd_executable +
            [REPO_UPDATE_SCRIPT] +
            getattr(context, 'extra_run_args', [])
        )
    elif cmd_parts[0] == "deploy_daemon":
        cmd_parts = (
            cmd_executable +
            [DEPLOY_DAEMON_SCRIPT] +
            getattr(context, 'extra_run_args', [])
        )
    else:
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
    except tds.exceptions.RunProcessError:
        pass

    context.process = proc


@given(u'I wait {number} seconds')
def given_i_wait_seconds(context, number):
    time.sleep(int(number))


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
