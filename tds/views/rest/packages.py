"""
REST API view for packages.
"""

from cornice.resource import resource, view
import jenkinsapi.jenkins
try:
    from jenkinsapi.custom_exceptions import JenkinsAPIException, NotFound
except ImportError:
    from jenkinsapi.exceptions import JenkinsAPIException, NotFound

import tds.model
from .base import BaseView, init_view
from .urls import ALL_URLS
from .permissions import PACKAGE_PERMISSIONS


@resource(collection_path=ALL_URLS['package_collection'],
          path=ALL_URLS['package'])
@init_view(name='package')
class PackageView(BaseView):
    """
    Package view. This object maps to the /applications/{name_or_id}/packages
    and /applications/{name_or_id}/packages/{version}/{revision} URLs.
    An object of this class is initalized to handle each request.
    The collection_* methods correspond to the /applications URL while the
    others correspond to the /applications/{name_or_id} URL.
    """

    param_routes = {}

    defaults = {
        'status': 'pending',
    }

    required_post_fields = ('version', 'revision')

    permissions = PACKAGE_PERMISSIONS

    individual_allowed_methods = dict(
        GET=dict(description="Get package for an application with version and "
                 "revision."),
        PUT=dict(description="Update package for an application with version "
                 "and revision."),
    )

    collection_allowed_methods = dict(
        GET=dict(description="Get a list of packages for an application, "
                 "optionally by limit and/or start."),
        POST=dict(description="Add a new package for an application."),
    )

    def __init__(self, *args, **kwargs):
        """
        Do some basic initialization.
        """
        if 'application_id' in self.types:
            del self.types['application_id']
        if 'application_id' in self.param_descriptions:
            del self.param_descriptions['application_id']
        super(PackageView, self).__init__(*args, **kwargs)

    def validate_individual_package(self, request):
        """
        Validate that the package being retrieved exists and the application
        that the package is being referenced by also exists.
        If the package exists, added it to self.request.validated[self.name].
        """
        self.get_obj_by_name_or_id('application')
        if 'application' in request.validated:
            self.get_pkg_by_version_revision()

    def validate_package_collection(self, request):
        """
        Validate that the application being used to reference packages exists
        and add all packages for that application at
        self.request.validated[self.plural].
        """
        self.get_obj_by_name_or_id('application')
        if 'application' in request.validated:
            self.get_pkgs_by_limit_start()

    def get_pkg_by_version_revision(self):
        """
        Validate that the package with the version, revision, and application
        in the request exists.
        Attach it at request.validated['package'] if it does.
        Attach an error with location='path', name='revision' and a
        description otherwise.
        This error with return a "400 Bad Request" response to this request.
        """
        try:
            version = int(self.request.matchdict['version'])
        except ValueError:
            self.request.errors.add(
                'path', 'version',
                'Version must be an integer'
            )
            return
        try:
            revision = int(self.request.matchdict['revision'])
        except ValueError:
            self.request.errors.add(
                'path', 'revision',
                'Revision must be an integer'
            )
            return
        try:
            pkg = tds.model.Package.get(
                application=self.request.validated['application'],
                version=self.request.matchdict['version'],
                revision=self.request.matchdict['revision'],
            )
        except KeyError:    # No request.validated['application'] entry
            raise tds.exceptions.TDSException(
                "No validated application when trying to locate package."
            )
        if pkg is None:
            self.request.errors.add(
                'path', 'revision',
                "Package with version {v} and revision {r} does"
                " not exist for this application.".format(
                    v=version,
                    r=revision,
                )
            )
            self.request.errors.status = 404
        else:
            self.request.validated['package'] = pkg

    def get_pkgs_by_limit_start(self):
        """
        Get all packages for the application request.validated['application'],
        optionally paginated by request.params['limit'] and
        request.params['start'] if those are non-null.
        """
        try:
            pkgs = tds.model.Package.query().filter(
                tds.model.Package.application == self.request.validated[
                    'application'
                ],
            ).order_by(tds.model.Package.id)
        except KeyError:    # No request.validated['application'] entry
            raise tds.exceptions.TDSException(
                "No validated application when trying to locate package."
            )
        else:
            self.request.validated['packages'] = pkgs
        self.get_collection_by_limit_start()

    def validate_package_put(self):
        """
        Validate a PUT request by preventing collisions over unique fields for
        packages.
        """
        if self.name not in self.request.validated:
            return

        if 'version' in self.request.validated_params or 'revision' in \
                self.request.validated_params:
            found_pkg = self.model.get(
                application=self.request.validated['application'],
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
                    'version' if 'version' in self.request.validated_params
                        else 'revision',
                    "Unique constraint violated. Another package for this"
                    " application with this version and revision already"
                    " exists."
                )
                self.request.errors.status = 409
            self._validate_jenkins_build()

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

    def validate_package_post(self):
        """
        Validate a POST request by preventing collisions over unique fields.
        """
        self.get_obj_by_name_or_id('application')
        app_check = 'application' in self.request.validated
        ver_check = 'version' in self.request.validated_params
        rev_check = 'revision' in self.request.validated_params
        if not (app_check and ver_check and rev_check):
            return
        found_pkg = self.model.get(
            application=self.request.validated['application'],
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

        if 'job' not in self.request.validated_params:
            self.request.validated_params['job'] = self.request.validated[
                'application'
            ].path

    def _add_jenkins_error(self, message):
        """
        Add a Jenkins error at 'job' or 'name_or_id' in that order.
        """
        if 'job' in self.request.validated_params:
            self.request.errors.add('query', 'job', message)
        else:
            self.request.errors.add('path', 'name_or_id', message)

    def _validate_jenkins_build(self):
        """
        Validate that a Jenkins build exists for a package being added or
        updated.
        """
        try:
            jenkins = jenkinsapi.jenkins.Jenkins(self.jenkins_url)
        except KeyError:
            raise tds.exceptions.ConfigurationError(
                'Could not find jenkins_url in settings file.'
            )
        except Exception:
            self._add_jenkins_error(
                "Unable to connect to Jenkins server at {addr} to check for "
                "package.".format(addr=self.jenkins_url)
            )
            self.request.errors.status = 500
            return

        if 'job' in self.request.validated_params:
            job_name = self.request.validated_params['job']
        elif self.name in self.request.validated and getattr(
            self.request.validated[self.name], 'job', None
        ):
            job_name = self.request.validated[self.name].job
        elif 'application' in self.request.validated:
            job_name = self.request.validated['application'].path
        else:
            # Unexpected, but if it happens, bail out.
            return

        if 'version' in self.request.validated_params:
            version = self.request.validated_params['version']
        elif self.name in self.request.validated:
            version = self.request.validated[self.name].version
        else:
            # Also unexpected. Bail out.
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
        except ValueError:
            return

        try:
            build = job.get_build(int(version))
        except (KeyError, JenkinsAPIException, NotFound):
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
        """
        Handle a POST request after the parameters are marked valid JSON.
        """
        self.request.validated_params['creator'] = self.request.validated[
            'user'
        ]
        return self._handle_collection_post()
