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
    def add(application, **_kwds):
        """Add an application."""
        app_name = application
        application = Application.get(name=app_name)
        if application is not None:
            raise tds.exceptions.AlreadyExistsError(
                "Application already exists: %s", application.name
            )

        log.debug('Creating application %r', app_name)
        return dict(result=Application.create(name=app_name))

    @validate('application')
    def delete(self, application, **_kwds):
        """Remove a given project."""
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
