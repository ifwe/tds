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

"""
Command and view resolver for TDS.
"""
import os
import pwd
import logging

import tds.authorize
import tds.commands
import tds.views
import tds.utils

from . import TDSProgramBase
from ..model import LocalActor


log = logging.getLogger('tds.main')


class TDS(TDSProgramBase):
    """TDS main class"""

    view = tds.views.CLI

    views = {
        ('deploy', 'fix'): 'deploy_promote',
    }

    def __init__(self, params):
        """Basic initialization"""
        super(TDS, self).__init__(params)
        self.params['deployment'] = True

    @tds.utils.debug
    def update_program_parameters(self):
        """Set some additional program parameters"""

        log.debug('Adding several additional parameters for program')

        self.params['user'] = pwd.getpwuid(os.getuid()).pw_name
        log.log(5, 'User is: %s', self.params['user'])

        self.params['user_level'] = self.authconfig.get_access_level(
            LocalActor()
        )
        log.log(5, 'User level is: %s', self.params['user_level'])

        self.params['env'] = self.config['env.environment']
        log.log(5, 'Environment is: %s', self.params['env'])

        self.params['jenkins_url'] = self.config['jenkins.url']

        self.params['mco_bin'] = self.config['mco.bin']

    @tds.utils.debug
    def execute_command(self):
        """Run the requested command for TDS"""

        log.debug('Running the requested command')
        command = self.params['command_name'].replace('-', '_')
        subcommand = self.params['subcommand_name'].replace('-', '_')
        full_command = (command, subcommand)
        controller_name = command.capitalize() + "Controller"
        log.log(5, 'Instantiating class %r', controller_name)

        view_name = self.views.get(
            full_command,
            '%s_%s' % full_command
        )

        ControllerClass = getattr(tds.commands, controller_name)
        controller = ControllerClass(self.config)

        result = controller.action(subcommand, **self.params)

        return self.render(view_name, result)

    def render(self, *args, **kwargs):
        """Render view."""
        return self.view(output_format=self.params['output_format']) \
            .generate_result(*args, **kwargs)
