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
        ('deploy', 'promote'),
        ('deploy', 'redeploy'),
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

        graphite.send(deployment.package.name, 1)
