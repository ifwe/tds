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

"""Utilities for determining authorization level of actors."""
import logging

import tds.utils

from tds.exceptions import AccessError

ACCESS_LEVELS = ['disabled', 'admin', 'prod', 'stage', 'dev']
DEFAULT_ACCESS_MAPPING = {
    'disabled': 'root',
    'admin': 'siteops',
    'prod': 'prodsupportlite',
    'stage': 'stagesupport',
    'dev': 'engteam',
}

log = logging.getLogger('tds')


class TDSAuthConfig(tds.utils.config.YAMLConfig):
    """
    TDS authorization configuration object.
    """

    def load(self):
        try:
            super(TDSAuthConfig, self).load()
        except tds.utils.config.ConfigurationError:
            self.update(dict(
                mapping=DEFAULT_ACCESS_MAPPING
            ))

    @property
    def access_levels(self):
        """Return acces levels."""
        return ACCESS_LEVELS

    @property
    def access_mapping(self):
        """Return mapping."""
        return self['mapping']

    def get_access_level(self, actor):
        """Find highest access level for user"""

        log.debug('Finding user\'s access level')

        log.log(5, 'User\'s groups are: %s', ', '.join(actor.groups))

        for level in self.access_levels:
            if self.access_mapping[level] in actor.groups:
                log.log(5, 'Returning level: %s', level)
                return level

        log.log(5, 'No matching level found for user')
        return None


@tds.utils.debug
def verify_access(user_level, access_level):
    """Ensure user has appropriate access"""

    log.debug('Ensuring user has necessary access')

    if user_level not in ACCESS_LEVELS or ACCESS_LEVELS.index(user_level) > \
            ACCESS_LEVELS.index(access_level):
        raise AccessError()
