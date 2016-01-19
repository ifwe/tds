"""Model module for deploy_info object."""

from .base import Base


class DeployInfo(Base):
    """Model base class for actor object."""

    def __init__(self, actor, action, project, package, target):
        """Initialize object."""
        super(DeployInfo, self).__init__()
        self.actor = actor
        self.action = action
        self.project = project
        self.package = package
        self.target = target
