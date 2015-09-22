"""
REST API view for packages retrieved by ID.
"""

from cornice.resource import resource, view
import jenkinsapi.jenkins
try:
    from jenkinsapi.custom_exceptions import JenkinsAPIException, NotFound
except ImportError:
    from jenkinsapi.exceptions import JenkinsAPIException, NotFound

import tds.model
from .base import BaseView, init_view

@resource(collection_path="/packages", path="/packages/{id}")
@init_view(name='package-by-id', model=tds.model.Package)
class PackageByIDView(BaseView):

    types = {
        'id': 'integer',
        'version': 'integer',
        'revision': 'integer',
        'status': 'choice',
        'builder': 'choice',
        'job': 'string',
        'name': 'string',
    }

    param_routes = {
        'name': 'pkg_name',
    }

    defaults = {
        'status': 'pending',
    }

    required_post_fields = ('version', 'revision', 'name')

    def validate_individual_package_by_id(self, request):
        self.get_obj_by_name_or_id(obj_type='Package', model=self.model,
                                   param_name='id', can_be_name=False,
                                   dict_name=self.name)

    def validate_package_by_id_put(self):
        self._validate_id("PUT", "package")
        if self.name not in self.request.validated:
            return

        if any(x in self.request.validated_params for x in
               ('version', 'revision', 'name')):
            found_pkg = self.model.get(
                application=tds.model.Application.get(
                    pkg_name=self.request.validated_params['name']
                ) if 'name' in self.request.validated_params else
                    self.request.validated[self.name].application,
                version=self.request.validated_params['version'] if 'version'
                    in self.request.validated_params else
                    self.request.validated[self.name].version,
                revision=self.request.validated_params['revision'] if
                    'revision' in self.request.validated_params else
                    self.request.validated[self.name].revision,
            )
            if found_pkg and found_pkg != self.request.validated[self.name]:
                self.request.errors.add(
                    'query',
                    'name' if 'name' in self.request.validated_params
                        else 'version' if 'version' in
                        self.request.validated_params else 'revision',
                    "Unique constraint violated. Another package for this"
                    " application with this version and revision already"
                    " exists."
                )
                self.request.errors.status = 409

        if any(x in self.request.validated_params for x in
               ('version', 'revision', 'job')):
            self._validate_jenkins_build()

        if self.name not in self.request.validated:
            return
        if 'status' in self.request.validated_params and \
                self.request.validated_params['status'] != \
                self.request.validated[self.name].status:
            if not (self.request.validated[self.name].status == 'failed' and
                    self.request.validated_params['status'] == 'pending'):
                self.request.errors.add(
                    'query', 'status',
                    "Cannot change status to {new} from {current}.".format(
                        new=self.request.validated_params['status'],
                        current=self.request.validated[self.name].status,
                    )
                )
                self.request.errors.status = 403

    def validate_package_by_id_post(self):
        self._validate_id("POST", "package")
        if 'name' not in self.request.validated_params:
            return
        found_app = tds.model.Application.get(
            pkg_name=self.request.validated_params['name']
        )
        ver_check = 'version' in self.request.validated_params
        rev_check = 'revision' in self.request.validated_params

        if not found_app:
            self.request.errors.add(
                'query', 'name',
                "Application with name {name} does not exist.".format(
                    name=self.request.validated_params['name']
                )
            )
            self.request.status = 400
            return
        elif not (ver_check and rev_check):
            return
        else:
            self.request.validated_params['application'] = found_app
        found_pkg = self.model.get(
            application=found_app,
            version=self.request.validated_params['version'],
            revision=self.request.validated_params['revision'],
        )

        if found_pkg:
            self.request.errors.add(
                'query', 'version',
                "Unique constraint violated. A package for this application"
                " with this version and revision already exists."
            )
            self.request.errors.status = 409
        if 'status' in self.request.validated_params and \
                self.request.validated_params['status'] != 'pending':
            self.request.errors.add(
                'query', 'status',
                "Status must be pending for new packages."
            )
            self.request.errors.status = 403

        self._validate_jenkins_build()

    def _add_jenkins_error(self, message):
        if 'job' in self.request.validated_params:
            self.request.errors.add('query', 'job', message)
        elif 'version' in self.request.validated_params:
            self.request.errors.add('query', 'version', message)
        elif 'name' in self.request.validated_params:
            self.request.errors.add('query', 'name', message)
        elif self.name in self.request.validated:
            self.request.errors.add('path', 'id', message)

    def _validate_jenkins_build(self):
        try:
            jenkins = jenkinsapi.jenkins.Jenkins(self.settings['jenkins_url'])
        except KeyError:
            raise tds.exceptions.ConfigurationError(
                'Could not find jenkins_url in settings file.'
            )
        except Exception:
            self._add_jenkins_error(
                "Unable to connect to Jenkins server at {addr} to check for "
                "package.".format(addr=self.settings['jenkins_url'])
            )
            self.request.errors.status = 500
            return

        application = None
        if 'name' in self.request.validated_params:
            app = tds.model.Application.get(
                pkg_name=self.request.validated_params['name']
            )
            if app is None:
                return
            application = app

        if 'job' in self.request.validated_params:
            job_name = self.request.validated_params['job']
        elif self.name in self.request.validated and getattr(
            self.request.validated[self.name], 'job', None
        ):
            job_name = self.request.validated[self.name].job
        elif application is not None:
            job_name = application.path
        else:
            return

        if 'version' in self.request.validated_params:
            version = self.request.validated_params['version']
        elif self.name in self.request.validated:
            version = self.request.validated[self.name].version
        else:
            return

        matrix_name = None
        if '/' in job_name:
            job_name, matrix_name = job_name.split('/', 1)

        try:
            job = jenkins[job_name]
        except KeyError:
            self._add_jenkins_error("Jenkins job {job} does not exist.".format(
                job=job_name,
            ))
            self.request.errors.status = 400
            return

        try:
            int(version)
        except:
            return

        try:
            build = job.get_build(int(version))
        except (KeyError, JenkinsAPIException, NotFound) as exc:
            self._add_jenkins_error(
                "Build with version {vers} for job {job} does not exist on "
                "Jenkins server.".format(vers=version, job=job_name)
            )
            self.request.errors.status = 400

        if matrix_name is not None:
            for run in build.get_matrix_runs():
                if matrix_name in run.baseurl:
                    build = run
                    break
            else:
                self._add_jenkins_error(
                    "No matrix run matching {matrix} for job {job} found."
                    .format(matrix=matrix_name, job=job_name)
                )
                self.request.errors.status = 400

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_obj_post', 'validate_cookie'))
    def collection_post(self):
        self.request.validated_params['creator'] = self.request.validated[
            'user'
        ]
        return self._handle_collection_post()
