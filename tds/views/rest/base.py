"""
Base view class for REST API.
"""

import json

from pyramid.response import Response

from .utils import get

from ..json_encoder import TDSEncoder


class BaseView(object):
    """
    This class manages & enforces permission and does basic initialization of
    views. It also handles validation for certain things.
    """

    #TODO: Add permissions system

    def __init__(self, request):
        """
        Set params for this request.
        See method corresponding the HTTP method below for details on expected
        parameters.
        Retrieve the name of the object class being viewed (e.g., 'package'
        for PackageView) and set it to self.name.
        """
        self.request = request
        self.name = self.__class__.__name__.split('View')[0].lower()

    @staticmethod
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
            raise NotImplementedError(
                "REST renderer not implemented: {r}.".format(
                    r=renderer,
                )
            )

    def validate_individual(self, request):
        """
        Validate that the project with given name exists and attach
        the project to the request at request.validated['project'].
        This validator can raise a "400 Bad Request" error.
        """
        if self.name == 'package':
            get.obj_by_name_or_id('application', request)
            if 'application' in request.validated:
                get.pkg_by_version_revision(request)
        else:
            get.obj_by_name_or_id(self.name, request)

    def validate_collection_get(self, request):
        """
        Make sure that the selection parameters are valid for projects.
        If they are not, raise "400 Bad Request".
        Else, set request.validated['projects'] to projects matching query.
        """
        if self.name == 'package':
            get.obj_by_name_or_id('application', request)
            if 'application' in request.validated:
                get.pkgs_by_limit_start(request)
        else:
            get.collection_by_limit_start(self.name, request)
