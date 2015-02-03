"""
Utility functions for REST API.
"""

import json

from pyramid.response import Response

from ..json_encoder import TDSEncoder


def make_response(body, status="200 OK", renderer="json"):
    """
    Make and return a Response with the given body and HTTP status code.
    """
    if renderer == "json":
        return Response(
            body=json.dumps(body, cls=TDSEncoder),
            content_type="text/json",
            status=status,
        )
    else:
        raise NotImplementedError("REST renderer not implemented: {r}".format(
            r=renderer,
        ))
