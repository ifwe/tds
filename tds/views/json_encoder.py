"""
JSON encoder for a few object types.
"""

import json
import datetime
from time import mktime

class TDSEncoder(json.JSONEncoder):

    def default(self, obj):
        """Return JSON serializable representation of obj."""
        # JSON standard doesn't specify datetime format.
        # Convert datetimes to ints:
        if isinstance(obj, datetime.datetime):
            return int(mktime(obj.timetuple()))

        # If iterable, convert to list:
        try:
            return list(obj)
        except:
            pass

        # If the object has a to_dict callable, call it:
        if callable(getattr(obj, 'to_dict', None)):
            return obj.to_dict()

        # Let JSONEncoder encode obj or throw TypeError if obj non-serializable
        return json.JSONEncoder.default(self, obj)
