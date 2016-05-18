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
JSON encoder for a few object types.
"""

import json
import datetime
from time import mktime


class TDSEncoder(json.JSONEncoder):
    """Custom JSON encoder for a few object types."""

    def default(self, obj):
        """Return JSON serializable representation of obj."""
        # JSON standard doesn't specify datetime format.
        # Convert datetimes to ints:
        if isinstance(obj, datetime.datetime):
            return int(mktime(obj.timetuple()))

        # If iterable, convert to list:
        try:
            return list(obj)
        except TypeError:
            pass

        # If the object has a to_dict callable, call it:
        if callable(getattr(obj, 'to_dict', None)):
            return obj.to_dict()

        # Let JSONEncoder encode obj or throw TypeError if obj non-serializable
        return json.JSONEncoder.default(self, obj)
