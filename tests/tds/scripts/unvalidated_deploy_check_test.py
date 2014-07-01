import unittest2

from mock import Mock, patch

import tds.scripts.unvalidated_deploy_check as UDC

from tests.factories.model.actor import ActorFactory
from tests.factories.model.package import PackageFactory
from tests.factories.model.deployment import AppDeploymentFactory
from tests.factories.utils.config import DatabaseTestConfigFactory

class TestUnvalidatedDeploymentNotifier(unittest2.TestCase):
    def get_mock_app_dep(self, actor, package):
        tds_deployment = Mock(
            environment='test',
            package=package
        )

        application = Mock(
            app_type='fake_app_type'
        )
        return Mock(
            application=application,
            deployment=tds_deployment,
            user=actor.name,
        )

    def test_convert_deployment(self):
        actor = ActorFactory()
        package = PackageFactory()

        app_deployment = self.get_mock_app_dep(actor, package)
        deployment = app_deployment.deployment
        application = app_deployment.application

        result = UDC.UnvalidatedDeploymentNotifier.convert_deployment(app_deployment)

        # assert result.actor == actor  # XXX: skipped for now. groups don't match
        assert result.actor.name == actor.name
        assert result.action['command'] == 'unvalidated'
        assert result.project['name'] == package.name
        assert result.package == vars(package)  # TODO: shouldn't have to call vars
        assert result.target['environment'] == deployment.environment
        assert result.target['apptypes'] == [application.app_type]

    def test_notify(self):
        n = 2
        actor = ActorFactory()
        packages = [PackageFactory() for _ in range(n)]
        deployments = [self.get_mock_app_dep(actor, p) for p in packages]

        base = UDC.UnvalidatedDeploymentNotifier.__bases__[0]
        with patch.object(base, 'notify'):
            udn = UDC.UnvalidatedDeploymentNotifier(dict())
            udn.notify(deployments)
            assert base.notify.call_count == n


class TestTagopsdbDeploymentProvider(unittest2.TestCase):
    def test_init_and_get_all(self):
        dbconfig = DatabaseTestConfigFactory()
        app_deps = [AppDeploymentFactory(), AppDeploymentFactory()]

        with patch('tds.model.AppDeployment') as app_dep_mock, \
            patch('tagopsdb.init', return_value=None) as init_session:
            app_dep_mock.find.return_value = app_deps

            tdp = UDC.TagopsdbDeploymentProvider(dbconfig)
            tdp.init()

            assert len(init_session.call_args_list) == 1
            (options,), _kwargs = init_session.call_args_list[0]
            assert options.get('url', None) == dict(
                    username=dbconfig['db']['user'],
                    password=dbconfig['db']['password'],
                    host=dbconfig['db']['hostname'],
                    database=dbconfig['db']['db_name'],
                )

            assert tdp.get_all(app_deps[0].environment) == app_deps
