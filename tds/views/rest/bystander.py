"""
REST API view for Bystander functionality.
This view supports only GET and HEAD and on a successfull GET request returns a
dict with app_id keys with dict values with keys:
    name: name of the application
    tier: a dict with tier_id keys with values:
        name: name of the tier
        prod_ahead: True iff prod version is ahead of stage version
        stage_ahead: True iff stage version is ahead of dev version
        envs: a dict with env_id keys with values:
            package_id: ID of the latest package deployed in given env on given
                tier for given app
            package_version: version of said package
            package_revision: revision of said package
            package_commit_hash: commit hash of said package
The full structure of the response is similar to:
    {
        1: {
            'name': 'app1',
            1: {
                name: 'tier1',
                prod_ahead: false,
                stage_ahead: false,
                1: {
                    package_id: 1,
                    package_version: 1,
                    package_revision: 1,
                    package_commit_hash: <some_hash>,
                },
                2: {
                    package_id: 1,
                    package_version: 1,
                    package_revision: 1,
                    package_commit_hash: <some_hash>,
                },
                3: {
                    package_id: 1,
                    package_version: 1,
                    package_revision: 1,
                    package_commit_hash: <some_hash>,
                }
            },
            2: {
                name: 'tier2',
                prod_ahead: false,
                stage_ahead: true,
                1: {
                    package_id: 1,
                    package_version: ,
                    package_revision: 1,
                    package_commit_hash: <some_hash>,
                },
                2: {
                    package_id: 2,
                    package_version: 2,
                    package_revision: 1,
                    package_commit_hash: <some_hash>,
                },
                3: {
                    package_id: 2,
                    package_version: 2,
                    package_revision: 1,
                    package_commit_hash: <some_hash>,
                }
            }
        },
        2: {
            'name': 'app2',
            3: {
                name: 'tier3',
                prod_ahead: true,
                stage_ahead: false,
                1: {
                    package_id: 3,
                    package_version: 1,
                    package_revision: 1,
                    package_commit_hash: <some_hash>,
                },
                2: {
                    package_id: 3,
                    package_version: 1,
                    package_revision: 1,
                    package_commit_hash: <some_hash>,
                },
                3: {
                    package_id: 4,
                    package_version: 2,
                    package_revision: 1,
                    package_commit_hash: <some_hash>,
                }
            },
            4: {
                name: 'tier4',
                prod_ahead: true,
                stage_ahead: true,
                1: {
                    package_id: 3,
                    package_version: 1,
                    package_revision: 1,
                    package_commit_hash: <some_hash>,
                },
                2: {
                    package_id: 4,
                    package_version: 2,
                    package_revision: 1,
                    package_commit_hash: <some_hash>,
                },
                3: {
                    package_id: 5,
                    package_version: 3,
                    package_revision: 1,
                    package_commit_hash: <some_hash>,
                }
            }
        }
    }
"""

from cornice.resource import resource, view

import tagopsdb.model
import tds.model
from . import base
from .urls import ALL_URLS
from .permissions import BYSTANDER_PERMISSIONS

DEV_ID = 1
STAGE_ID = 2
PROD_ID = 3


@resource(path=ALL_URLS['bystander'])
class BystanderView(base.BaseView):
    """
    Bystander view.
    """

    permissions = BYSTANDER_PERMISSIONS

    def validate_bystander_get(self, _request):
        """
        Validate a bystander GET request.
        """
        self.name = 'bystander'
        self._validate_params(list())

        self.result = dict()
        all_envs = tagopsdb.model.Environment.all()
        for app_tier in tagopsdb.model.ProjectPackage.all():
            app = tds.model.Application.get(id=app_tier.pkg_def_id)
            tier = tds.model.AppTarget.get(id=app_tier.app_id)
            env_sub_dict = dict()
            for env in all_envs:
                env_dep = app.get_latest_completed_tier_deployment(
                    tier.id,
                    env.id,
                    query=self.query(tagopsdb.model.AppDeployment),
                )
                if env_dep is not None:
                    env_sub_dict[env.id] = dict(
                        name=env.env,
                        package_id=env_dep.package_id,
                        package_version=env_dep.package.version,
                        package_revision=env_dep.package.revision,
                        package_commit_hash=env_dep.package.commit_hash,
                    )
            if len(env_sub_dict) == 0:
                continue
            if app.id not in self.result:
                self.result[app.id] = dict(name=app.name)
            try:
                env_sub_dict['prod_ahead'] = env_sub_dict[PROD_ID][
                    'package_version'
                ] > env_sub_dict[STAGE_ID]['package_version']
            except KeyError:
                env_sub_dict['prod_ahead'] = False
            try:
                env_sub_dict['stage_ahead'] = env_sub_dict[STAGE_ID][
                    'package_version'
                ] > env_sub_dict[DEV_ID]['package_version']
            except KeyError:
                env_sub_dict['stage_ahead'] = False
            self.result[app.id][tier.id] = env_sub_dict
            self.result[app.id][tier.id]['name'] = tier.name

    def validate_bystander_options(self, _request):
        """
        Validate bystander OPTIONS request.
        """
        self.result = dict(
            GET=dict(
                description="Get latest deployed version of all applications"
                    " on all associated tiers in each environment.",
                parameters=dict(),
            ),
            HEAD=dict(description="Do a GET query without a body returned."),
            OPTIONS=dict(
                descriptoin="Get HTTP method options and parameters for this "
                    "URL endpoint.",
            )
        )

    @view(validators=('validate_bystander_get', 'validate_cookie'))
    def get(self):
        """
        Performa a GET request after all validation has passed.
        """
        return self.make_response(self.to_json_obj(self.result))

    @view(validators=('validate_bystander_get', 'validate_cookie'))
    def head(self):
        """
        Same as get above except returns empty body.
        """
        return self.make_response(renderer="empty")

    @view(validators=('validate_bystander_options',))
    def options(self):
        """
        Perform an OPTIONS request after all validation has passed.
        """
        return self.make_response(
            body=self.to_json_obj(self.result),
            headers=dict(Allows="GET, HEAD, OPTIONS"),
        )

    @view(validators=('method_not_allowed'))
    def delete(self):
        """
        Perform a DELETE request after all validation has passed.
        """
        return self.make_response({})

    @view(validators=('method_not_allowed'))
    def put(self):
        """
        Perform a PUT after all validation has passed.
        """
        return self.make_response({})
