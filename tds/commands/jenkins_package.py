'Support for adding a package directly from a Jenkins instance'

import os.path
import jenkinsapi.jenkins
try:
    from jenkinsapi.custom_exceptions import JenkinsAPIException, NotFound
except ImportError:
    from jenkinsapi.exceptions import JenkinsAPIException, NotFound

from .package import Package


class Jenkinspackage(Package):

    """Temporary class to manage packages for supported applications
       via direct access to Jenkins build (artifactory)
    """

    def _queue_rpm(self, params, queued_rpm, rpm_name, app):
        """Move requested RPM into queue for processing"""

        buildnum = int(params['version'])
        job_name = params['job_name']

        # XXX: use config
        jenkins = jenkinsapi.jenkins.Jenkins('https://ci.tagged.com/')

        try:
            build = jenkins[job_name].get_build(buildnum)
            artifacts = build.get_artifact_dict()[rpm_name]
            data = artifacts.get_data()
        except (
            KeyError,
            JenkinsAPIException,
            NotFound
        ) as e:
            self.log.error(e)
            return False

        tmpname = os.path.join(os.path.dirname(os.path.dirname(queued_rpm)),
                               'tmp', rpm_name)

        with open(tmpname, 'wb') as tmp_rpm:
            tmp_rpm.write(data)
            tmp_rpm.close()
            os.link(tmp_rpm.name, queued_rpm)
            os.unlink(tmp_rpm.name)

        return True
