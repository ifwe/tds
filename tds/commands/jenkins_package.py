'Support for adding a package directly from a Jenkins instance'

import os.path
import jenkinsapi.jenkins
try:
    from jenkinsapi.custom_exceptions import JenkinsAPIException, NotFound
except ImportError:
    from jenkinsapi.exceptions import JenkinsAPIException, NotFound

from .package import PackageController

import logging

log = logging.getLogger('tds')


class JenkinspackageController(PackageController):
    """Temporary class to manage packages for supported applications
       via direct access to Jenkins build (artifactory)
    """

    def _queue_rpm(self, params, queued_rpm, rpm_name, app):
        """Move requested RPM into queue for processing"""

        buildnum = int(params['version'])
        job_name = params['job_name']

        try:
            jenkins = jenkinsapi.jenkins.Jenkins(params['jenkins_url'])
        except Exception:
            raise Exception(
                'Unable to contact Jenkins server "%s"',
                params['jenkins_url']
            )

        try:
            job = jenkins[job_name]
        except Exception:
            raise Exception('Job "%s" not found', job_name)

        try:
            build = job.get_build(buildnum)
        except (
            KeyError,
            JenkinsAPIException,
            NotFound
        ) as exc:
            log.error(exc)
            raise Exception(
                'Build "%s@%s" does not exist on %s',
                params['job_name'],
                params['version'],
                params['jenkins_url']
            )

        try:
            artifacts = build.get_artifact_dict()[rpm_name]
            data = artifacts.get_data()
        except (
            KeyError,
            JenkinsAPIException,
            NotFound
        ):
            raise Exception(
                'Artifact not found for "%s@%s" on %s',
                params['job_name'],
                params['version'],
                params['jenkins_url']
            )

        tmpname = os.path.join(os.path.dirname(os.path.dirname(queued_rpm)),
                               'tmp', rpm_name)

        for tmpfile in (tmpname, queued_rpm):
            tmpdir = os.path.dirname(tmpfile)
            if not os.path.isdir(tmpdir):
                os.makedirs(tmpdir)

        with open(tmpname, 'wb') as tmp_rpm:
            tmp_rpm.write(data)

        os.link(tmpname, queued_rpm)
        os.unlink(tmpname)

        return True
