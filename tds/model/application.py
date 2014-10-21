"""Model module for application object."""

from .base import Base
import tagopsdb


class Application(Base):
    """Represents a single application."""
    # name
    # path
    # build_host
    # environment
    # packages / versions

    delegate = tagopsdb.PackageDefinition

    @property
    def targets(self):
        """Return deploy targets, but ignore the "dummy" target."""
        from .deploy_target import AppTarget
        return [
            AppTarget(delegate=x)
            for x in self.delegate.targets
            if x.name != x.dummy
        ]


    def get_version(self, version, revision='1'):
        from . import Package
        return Package.get(name=self.name, version=version, revision=revision)

    def create_version(self, version, revision, creator, **attrs):
        from . import Package

        defaults = dict(
            pkg_def_id=self.id,
            name=self.name,
            version=version,
            revision=revision,
            status='pending',
            creator=creator,
            builder=self.build_type,
            project_type='application'
        )

        defaults.update(attrs)
        return Package.create(**defaults)
