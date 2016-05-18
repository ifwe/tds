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

'''
Factories to create various tds.model.project.Project instances
'''
import factory
import tds.model.project as p
from .application import ApplicationFactory
# from .deploy_target import AppTargetFactory
#
# class _ProjectDelegate(object):
#     targets = [AppTargetFactory(name="targ1"),
#                AppTargetFactory(name="targ2")]


class ProjectFactory(factory.Factory):
    '''
    Package for the following command:

    `tds package add fake_package badf00d`
    by user 'fake_user'.
    '''
    FACTORY_FOR = p.Project

    name = 'fake_project'
    package_definitions = [ApplicationFactory(name="app1", path='/job/app1'),
                           ApplicationFactory(name="app2", path='/job/app2')]


    # delegate = _ProjectDelegate()
