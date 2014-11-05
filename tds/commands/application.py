"""Commands to manage the TDS applications."""
import logging

import tds.exceptions
from tds.model import Application
from .base import BaseController, validate

log = logging.getLogger('tds')


class ApplicationController(BaseController):
    """Commands to manage TDS applications."""

    access_levels = dict(
        list='environment',
        add='admin',
        delete='admin',
    )

    @staticmethod
    def add(application, job_name, deploy_type, arch, build_type, build_host,
            **_kwds):
        """Add an application."""

        app_name = application
        application = Application.get(name=app_name)
        if application is not None:
            raise tds.exceptions.AlreadyExistsError(
                "Application already exists: %s", application.name
            )

        Application.verify_package_arch(arch)
        Application.verify_build_type(build_type)

        log.debug('Creating application %r', app_name)

        # NOTE: create() does not give a proper exception/traceback
        # if there's missing keyword information
        return dict(result=Application.create(
            name=app_name,
            deploy_type=deploy_type,
            validation_type='matching',
            path=job_name,
            arch=arch,
            build_type=build_type,
            build_host=build_host
        ))

    @validate('application')
    def delete(self, application, **_kwds):
        """Remove a given application."""

        if len(application.targets):
            raise tds.exceptions.AssociatedTargetsError(
                'Application "%s" has associated targets: %s',
                application.name,
                ', '.join(x.name for x in application.targets)
            )

        log.debug('Removing application %r', application.name)
        application.delete()

        return dict(result=application)

    @validate('application')
    def list(self, applications=(), **_kwds):
        """Show information for requested applications
           (or all applications).
        """

        if len(applications) == 0:
            applications = Application.all()

        return dict(result=applications)
