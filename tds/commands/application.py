"""Commands to manage the TDS applications."""
import logging

import tagopsdb
import tagopsdb.deploy.repo
import tds.exceptions

from tds.model import Application
from .base import BaseController, validate

log = logging.getLogger('tds')


class ApplicationController(BaseController):
    """Commands to manage TDS applications."""

    access_levels = dict(
        add='admin',
        add_apptype='admin',
        delete='admin',
        delete_apptype='admin',
        list='environment',
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
    @validate('project')
    def add_apptype(self, project, application, apptypes, **_params):
        """Add a specific application type (or types) to the given project
           and application pair
        """

        log.debug('Adding application type(s) for a given '
                  'project/application pair')

        # Validate apptypes (targets) first and get target objects
        targets = []

        for apptype in apptypes:
            target = tds.model.AppTarget.get(name=apptype)

            if target is None:
                raise tds.exceptions.NotFoundError('Deploy target', [apptype])
            elif tagopsdb.model.ProjectPackage.get(
                project_id=project.id,
                app_id=target.id,
                pkg_def_id=application.id
            ) is not None:
                raise tds.exceptions.InvalidOperationError(
                    'Apptype "%s" is already a part of the project "%s" and '
                    'application "%s" pair',
                    apptype, project.name, application.name
                )
            else:
                targets.append(target)

        tagopsdb.deploy.repo.add_project_package_mapping(
            project, application, targets
        )
        tagopsdb.Session.commit()
        log.debug('Committed database changes')

        return dict(
            result=dict(
                application=application.name,
                project=project.name,
                targets=apptypes,
            )
        )

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

    @validate('targets')
    @validate('application')
    @validate('project')
    def delete_apptype(self, project, application, apptypes, **_params):
        """Delete a specific application type (or types) from the given
           project and application pair
        """

        # TODO: This needs to be properly written to avoid removing
        #       apptypes that still have active deployments
        pass

        tagopsdb.deploy.repo.delete_project_packages_mapping(
            project, application, apptypes
        )

        tagopsdb.Session.commit()

        return dict(
            result=dict(
                application=application.name,
                project=project.name,
                targets=apptypes,
            )
        )

    @validate('application')
    def list(self, applications=(), **_kwds):
        """Show information for requested applications
           (or all applications).
        """

        if len(applications) == 0:
            applications = Application.all()

        return dict(result=applications)
