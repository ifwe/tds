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

"""User configuration for feature tests"""

import yaml
import os
import grp

from behave import given


def get_groupname():
    """Get groupname of current process"""

    return grp.getgrgid(os.getegid()).gr_name


@given(u'I have "{level}" permissions')
def given_i_have_permissions(context, level):
    auth_conf = None
    with open(context.AUTH_CONFIG_FILE) as f:
        auth_conf = yaml.load(f.read())

    auth_conf['mapping'][level] = get_groupname()
    with open(context.AUTH_CONFIG_FILE, 'w') as f:
        f.write(yaml.dump(auth_conf))

    context.extra_run_args += ['--auth-config', context.AUTH_CONFIG_FILE]
