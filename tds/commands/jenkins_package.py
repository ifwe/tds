import os.path

from .package import Package


class Jenkinspackage(Package):

    """Temporary class to manage packages for supported applications
       via direct access to Jenkins build (artifactory)
    """

    def _queue_rpm(self, params, queued_rpm, rpm_name, app):
        """Move requested RPM into queue for processing"""

        buildnum = int(params['version'])
        job_name = params['job_name']

        # Late import to prevent hard dependency
        # XXX: is this really worth it?
        from jenkinsapi.jenkins import Jenkins
        from jenkinsapi.exceptions import JenkinsAPIException, NotFound

        J = Jenkins('https://ci.tagged.com/')  # XXX: use config

        try:
            a = J[job_name].get_build(buildnum).get_artifact_dict()[rpm_name]
            data = a.get_data()
        except (JenkinsAPIException, KeyError, NotFound) as e:
            self.log.error(e)
            return False

        tmpname = os.path.join(os.path.dirname(os.path.dirname(queued_rpm)),
                               'tmp', rpm_name)

        with open(tmpname, 'wb') as f:
            f.write(data)
            f.close()
            os.link(f.name, queued_rpm)
            os.unlink(f.name)

        return True
