"""Commands to manage the TDS applications."""
import logging

import tagopsdb
import tagopsdb.deploy.repo
import tds.exceptions
import tds.model

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
        update='environment',
    )

    @staticmethod
    def add(application, job_name, deploy_type, arch, build_type, build_host,
            **_kwds):
        """Add an application."""

        app_name = application
        application = tds.model.Application.get(name=app_name)
        if application is not None:
            raise tds.exceptions.AlreadyExistsError(
                "Application already exists: %s", application.name
            )

        tds.model.Application.verify_arch(arch)
        tds.model.Application.verify_build_type(build_type)

        log.debug('Creating application %r', app_name)

        # NOTE: create() does not give a proper exception/traceback
        # if there's missing keyword information
        return dict(result=tds.model.Application.create(
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
                ', '.join([x.name for x in application.targets])
            )

        log.debug('Removing application %r', application.name)
        application.delete()

        return dict(result=application)

    @validate('targets')
    @validate('application')
    @validate('project')
    def delete_apptype(self, application, project, apptypes, **_params):
        """Delete a specific application type (or types) from the given
           project and application pair
        """

        assert len(apptypes) == 1, "too many apptypes: %r" % apptypes
        apptype = apptypes[0]

        # Check for active host deployments
        host_deps = tds.model.HostDeployment.all(
            order_by='realized', desc=True
        )

        for host_dep in host_deps:
            if host_dep.application != application:
                continue

            if host_dep.app_target != apptype:
                continue

            if host_dep.status == 'failed':
                continue

            if host_dep.host_state == 'operational':
                raise tds.exceptions.InvalidOperationError(
                    'Apptype "%s" still has active deployments',
                    apptype.name
                )

        # Check for active tier deployments
        app_deps = tds.model.AppDeployment.find(
            target=apptype, order_by='realized', desc=True
        )
        app_target = tds.model.AppTarget.get(name=apptype.name)

        for app_dep in app_deps:
            if app_dep.application != application:
                continue

            if app_dep.status == 'invalidated':
                continue

            for app_host in app_target.hosts:
                if app_host.state == 'operational':
                    raise tds.exceptions.InvalidOperationError(
                        'Apptype "%s" still has active deployments',
                        apptype.name
                    )

        apptype.remove_application(application, project=project)

        return dict(
            result=dict(
                application=application,
                project=project,
                target=apptype,
            )
        )

    @validate('application')
    def list(self, applications=(), **_kwds):
        """Show information for requested applications
           (or all applications).
        """

        if len(applications) == 0:
            applications = tds.model.Application.all()

        return dict(result=applications)

    @staticmethod
    def _parse_properties(properties, valid_attrs=None, mappings=None):
        """
        Parse properties for the update function.
        properties should be a string of the following form:
            'attr1=val1 attr2=val2 ...'
        valid_attrs should be an iterable. If valid_attrs is None, no checks
        will be performed on the validity of an attr.
        mappings should be a dictionary that maps attrs to their appropriate
        names for use. If no mappings are passed, no mappings are made.
        Note: attrs are checked against valid_attrs, not mappings of attrs.
        """
        parsed = dict()
        for declaration in properties:
            try:
                attr, val = declaration.split('=', 1)
            except ValueError:
                raise tds.exceptions.InvalidInputError(
                    ("Invalid properties: %s. Split on '=' once for the "
                     "declaration %s returned 1 argument, expected 2"),
                    properties,
                    declaration,
                )
            if mappings and attr in mappings:
                mapped_attr = mappings[attr]
            else:
                mapped_attr = attr
            if valid_attrs and attr not in valid_attrs:
                raise tds.exceptions.InvalidInputError(
                    "Invalid attribute: %s. Valid attributes are: %r",
                    attr, valid_attrs
                )
            elif mapped_attr in parsed:
                raise tds.exceptions.InvalidInputError(
                    "Attribute appeared more than once: %s", attr
                )
            parsed[mapped_attr] = val
        return parsed

    @validate('application')
    def update(self, application, properties, **kwargs):
        """
        Update an existing application's properties.
        properties should be a string of the following form:
            'attr1=val1 attr2=val2 ...'
        """
        if kwargs['user_level'] == "admin":
            valid_attrs = (
                'name', 'deploy_type', 'arch', 'build_type', 'build_host',
                'job_name', 'repository'
            )
        else:
            valid_attrs = ('job_name', 'repository')
        mappings = dict(job_name="path")
        properties = self._parse_properties(properties, valid_attrs, mappings)
        updated = False

        for attr in properties:
            if getattr(application, attr) != properties[attr]:
                meth = getattr(tds.model.Application, 'verify_%s' % attr,
                               None)
                if meth is not None:
                    meth(properties[attr])
                setattr(application, attr, properties[attr])
                updated = True

        if updated:
            tagopsdb.Session.commit()
            return dict(result=application)
        else:
            raise tds.exceptions.InvalidOperationError(
                ("Update values match current values for application %s. "
                 "Nothing to do."),
                application.name
            )
