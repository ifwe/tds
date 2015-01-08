"""Model module for application object."""

from .base import Base
import tagopsdb
import tds.exceptions


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
            for x in self.delegate.applications
            if x.name != x.dummy
        ]

    @staticmethod
    def verify_arch(arch):
        """Ensure architecture for package is supported."""

        table = tagopsdb.model.PackageDefinition.__table__
        arches = table.columns['arch'].type.enums

        if arch not in arches:
            raise tds.exceptions.InvalidInputError(
                "Invalid architecture: %s. Should be one of: %s",
                arch,
                u', '.join(sorted(arches))
            )

    @staticmethod
    def verify_build_type(build_type):
        """Ensure architecture for package is supported."""

        table = tagopsdb.model.PackageDefinition.__table__
        build_types = table.columns['build_type'].type.enums

        if build_type not in build_types:
            raise tds.exceptions.InvalidInputError(
                "Invalid build type: %s. Should be one of: %s",
                build_type,
                u', '.join(sorted(build_types))
            )

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
