class DeployStrategy(object):
    def __init__(self, log):
        self.log = log

    def deploy_to_host(self, dep_host, app, version, retry=4):
        raise NotImplementedError

    def restart_host(self, dep_host, app, retry=4):
        raise NotImplementedError
