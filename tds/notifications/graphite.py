'''
Notifier and helpers for sending notifications via graphite
'''
import graphiteudp

from .base import Notifications, Notifier


@Notifications.add('graphite')
class GraphiteNotifier(Notifier):
    '''
    Send graphite notification
    '''
    active_events = (
        ('deploy', 'fix'),
        ('deploy', 'promote'),
        ('deploy', 'rollback')
    )

    def notify(self, deployment):
        event = (
            deployment.action.get('command'),
            deployment.action.get('subcommand')
        )
        if event not in self.active_events:
            return

        graphite = graphiteudp.GraphiteUDPClient(
            host=self.config['host'],
            port=self.config['port'],
            prefix=self.config['prefix']
        )

        if deployment.app_deployments:
            package = deployment.app_deployments[0].package
        else:
            package = deployment.host_deployments[0].package

        graphite.send(package.name, 1)
