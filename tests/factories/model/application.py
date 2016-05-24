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
Factories to create various tds.model.application.Application instances
'''
import factory
import tds.model.application as a


class ApplicationFactory(factory.Factory):
    '''
    Application
    '''
    FACTORY_FOR = a.Application

    name = 'fake_package'
    path = '/job/fake_package'
    build_host = 'ci.fake.com'
    environment = False
    pkg_name = name
    deploy_type = 'fake_dep'
    arch = 'fake_arch'
    build_type = 'fake_build'
