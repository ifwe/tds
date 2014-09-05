"""
Base class and helpers for tds.views
"""

import json

from .json_encoder import TDSEncoder


class Base(object):
    """Base class and interface for a tds.views class."""

    def __init__(self, output_format):
        """Initialize object."""
        self.output_format = output_format

    def generate_result(self, view_name, tds_result):
        """
        Create something useful for the user which will be returned
        to the main application entry point.
        """
        raise NotImplementedError

    def generate_json(self, iterable=None, obj=None):
        """
        Convert either iterable or obj to JSON.

        obj and items in iterable should have to_dict() methods that return
        a dictionary of fields and values.

        If both iterable and obj are None, return the empty array "[]".
        """
        if iterable is not None:
            return json.dumps([item.to_dict() for item in iterable
                               if not isinstance(item, Exception)],
                               cls=TDSEncoder)
        elif obj is not None:
            return json.dumps(obj.to_dict(), cls=TDSEncoder)
        else:
            return "[]"
