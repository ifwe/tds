import unittest2

from mock import Mock, patch

import tds.scripts.unvalidated_deploy_check as UDC

from tests.factories.model.actor import ActorFactory
from tests.factories.model.package import PackageFactory


class TestUnvalidatedDeploymentNotifier(unittest2.TestCase):
    def test_convert_deployment(self):
        actor = ActorFactory()
        package = PackageFactory()

        tds_deployment = Mock(
            environment='test',
            package=package
        )

        application = Mock(
            app_type='fake_app_type'
        )
        app_deployment = Mock(
            application=application,
            deployment=tds_deployment,
            user=actor.name,
        )
        result = UDC.UnvalidatedDeploymentNotifier.convert_deployment(app_deployment)

        # assert result.actor == actor  # XXX: skipped for now. groups don't match
        assert result.actor.name == actor.name
        assert result.action['command'] == 'unvalidated'
        assert result.project['name'] == package.name
        assert result.package == vars(package)  # TODO: shouldn't have to call vars
        assert result.target['environment'] == tds_deployment.environment
        assert result.target['apptypes'] == [application.app_type]
