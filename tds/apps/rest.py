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

import tds.views.rest

from tds.apps import TDSProgramBase


# Initialize connection to database (for session handling)
rest_api = TDSProgramBase({'user_level': 'admin'})
rest_api.initialize_db()

application = tds.views.rest.config.make_wsgi_app()
