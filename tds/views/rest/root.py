"""
REST API root view. Returns all URLs supported.
"""

from cornice.resource import resource, view

from .base import BaseView
from .urls import ALL_URLS


@resource(path="/")
class RootView(BaseView):
    """
    Root view. GET Returns all URLs supported. OPTIONS returns documentation.
    """

    name = 'root'

    urls = [
        dict(
            url=ALL_URLS['application_tier_collection'],
            description='Collection of all tiers associated with the project '
                'and application selected.',
        ),
        dict(
            url=ALL_URLS['application_tier'],
            description='Individual project-application-tier associations.',
        ),
        dict(
            url=ALL_URLS['application_collection'],
            description='Collection of all applications.',
        ),
        dict(
            url=ALL_URLS['application'],
            description='Individual application.',
        ),
        dict(
            url=ALL_URLS['current_host_deployment'],
            description='Current host deployment of the application on the '
                'host.',
        ),
        dict(
            url=ALL_URLS['current_tier_deployment'],
            description='Current tier deployment of the application on the '
                'tier in the environment.',
        ),
        dict(
            url=ALL_URLS['deployment_collection'],
            description='Collection of deployments.',
        ),
        dict(
            url=ALL_URLS['deployment'],
            description='Individual deployment.',
        ),
        dict(
            url=ALL_URLS['environment_collection'],
            description='Collection of environments.',
        ),
        dict(
            url=ALL_URLS['environment'],
            description='Individual environment.',
        ),
        dict(
            url=ALL_URLS['ganglia_collection'],
            description='Collection of Ganglias.',
        ),
        dict(
            url=ALL_URLS['ganglia'],
            description='Individual Ganglia.',
        ),
        dict(
            url=ALL_URLS['hipchat_collection'],
            description='Collection of HipChats.',
        ),
        dict(
            url=ALL_URLS['hipchat'],
            description='Individual HipChat.',
        ),
        dict(
            url=ALL_URLS['host_deployment_collection'],
            description='Collection of host deployments.',
        ),
        dict(
            url=ALL_URLS['host_deployment'],
            description='Individual host deployment.',
        ),
        dict(
            url=ALL_URLS['host_collection'],
            description='Collection of hosts.',
        ),
        dict(
            url=ALL_URLS['host'],
            description='Individual host.',
        ),
        dict(
            url=ALL_URLS['login'],
            description='Get a session cookie for non-OPTIONS requests.'
        ),
        dict(
            url=ALL_URLS['package_by_id_collection'],
            description='Collection of packages.',
        ),
        dict(
            url=ALL_URLS['package_by_id'],
            description='Individual package.',
        ),
        dict(
            url=ALL_URLS['package_collection'],
            description='Collection of packages for the application.',
        ),
        dict(
            url=ALL_URLS['package'],
            description='Package specified by the application, version, and '
                'revision.',
        ),
        dict(
            url=ALL_URLS['project_collection'],
            description='Collection of projects.',
        ),
        dict(
            url=ALL_URLS['project'],
            description='Individual project.',
        ),
        dict(
            url=ALL_URLS['search'],
            description='Search for objects of type obj_type.',
            obj_type_choices=[
                'application',
                'application_tier',
                'deployment',
                'environment',
                'ganglia',
                'hipchat',
                'host',
                'host_deployment',
                'package',
                'project',
                'tier',
                'tier_deployment',
            ],
        ),
        dict(
            url=ALL_URLS['tier_deployment_collection'],
            description='Collection of tier deployments.',
        ),
        dict(
            url=ALL_URLS['tier_deployment'],
            description='Individual tier deployment.',
        ),
        dict(
            url=ALL_URLS['tier_hipchat_collection'],
            description='Collection of HipChats associated with the tier.',
        ),
        dict(
            url=ALL_URLS['tier_hipchat'],
            description='A HipChat association with a tier.',
        ),
        dict(
            url=ALL_URLS['tier_collection'],
            description='Collection of tiers.',
        ),
        dict(
            url=ALL_URLS['tier'],
            description='Individual tier.',
        ),
    ]

    def validate_root_get(self, _request):
        """
        Set all the URLs to self.results.
        """
        self.results = self.urls

    def validate_root_options(self, _request):
        """
        Construct the OPTIONS response dict and set it to self.results.
        """
        self.result = dict(
            GET=dict(
                description="Get all supported URLS.",
            ),
            OPTIONS=dict(
                description="Get HTTP method options and parameters for this "
                    "URL endpoint.",
            )
        )

    @view(validators=('validate_root_get',))
    def get(self):
        """
        Perform a GET request all validation has passed.
        """
        return self.make_response([self.to_json_obj(x) for x in self.results])

    @view(validators=('validate_root_options',))
    def options(self):
        """
        Perform an OPTIONS request after all validation has passed.
        """
        return self.make_response(
            body=self.to_json_obj(self.result),
            headers=dict(Allows="GET, OPTIONS"),
        )

    @view(validators=('method_not_allowed',))
    def put(self):
        """
        Method not allowed.
        """
        pass
