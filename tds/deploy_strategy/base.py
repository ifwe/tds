"""
Abstract base DeployStrategy class.
"""


class DeployStrategy(object):
    """Abstract base DeployStrategy class."""

    def deploy_to_host(self, dep_host, app, version, retry=4):
        """Raise NotImplementedError."""
        raise NotImplementedError

    def restart_host(self, dep_host, app, retry=4):
        """Raise NotImplementedError."""
        raise NotImplementedError
