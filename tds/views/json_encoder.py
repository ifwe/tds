"""
JSON encoder for a few object types.
"""

import json
import datetime
from time import mktime

class TDSEncoder(json.JSONEncoder):

    def default(self, obj):
        # JSON standard doesn't specify datetime format.
        if isinstance(obj, datetime.datetime):
            return int(mktime(obj.timetuple()))
        return json.JSONEncoder.default(self, obj)
