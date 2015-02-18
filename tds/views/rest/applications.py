"""
REST API view for applications.
"""

from cornice.resource import resource

import tds.model
from .base import BaseView


@resource(collection_path="/applications", path="/applications/{name_or_id}")
class ApplicationView(BaseView):
    """
    Application view. This object maps to the /applications and
    /applications/{name_or_id} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /applications URL while the
    others correspond to the /applications/{name_or_id} URL.
    """

    name = 'application'
    plural = 'applications'
    model = tds.model.Application
