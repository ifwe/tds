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

import json
import os

import salt.config


class SMinion(object):
    """Fake salt.minion.SMinion class"""

    INPUT_FILE = 'salt-input.json'
    RESULTS_FILE = 'salt-results.json'

    def __init__(self, opts):
        self.functions = {
            'publish.full_data': self.return_full_data,
        }

    # Emulate actual call to tds module
    def read_input(self):
        work_dir = os.environ.get('BEHAVE_WORK_DIR', os.getcwd())
        input_file = os.path.join(work_dir, self.INPUT_FILE)

        input_data = {}
        if os.path.isfile(input_file):
            with open(input_file) as f:
                input_data = json.loads(f.read())

        return input_data

    def record_results(self, stuff):
        work_dir = os.environ.get('BEHAVE_WORK_DIR', os.getcwd())
        results_file = os.path.join(work_dir, self.RESULTS_FILE)

        old_data = []

        if os.path.isfile(results_file):
            with open(results_file) as f:
                old_data = json.loads(f.read())

        old_data.extend(stuff)

        with open(results_file, 'wb') as f:
            f.write(json.dumps(old_data))

    def install(self, hostname, app, version):
        return dict(
            hostname=hostname,
            package=app,
            version=version,
            restart=False,
            exitcode=0,
            result='Install of app "%s", version "%s" successful'
                   % (app, version),
        )

    def restart(self, hostname, app):
        return dict(
            hostname=hostname,
            package=app,
            version=None,
            restart=True,
            exitcode=0,
            result='Restart of app "%s" successful' % app,
        )

    def return_full_data(self, *args, **kwargs):
        (host_re, command), (args,) = args[:2], args[2:]
        hostname = host_re[:-2]   # Remove '.*' to get hostname

        input = self.read_input()

        if hostname in input:
            result = input[hostname]
        elif command == 'tds.restart':
            result = self.restart(hostname, *args)
        elif command == 'tds.install':
            result = self.install(hostname, *args)
        else:
            raise Exception('Unknown command:%r', command)

        self.record_results([result])

        return dict(
            hostname=dict(
                ret=result['result'],
            ),
        )


class Caller(object):
    """Fake salt.client.Caller class"""

    def __init__(self, c_path='/etc/salt/minion', mopts=None):
        if mopts:
            self.opts = mopts
        else:
            self.opts = salt.config.minion_config(c_path)
        self.sminion = SMinion(self.opts)
