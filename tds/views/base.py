"""
Base class and helpers for tds.views
"""


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
