"""
Script to check and enforce that the environment reflects the database state.
"""

import pprint
import salt.client
import salt.config

import tds.model
import tds.apps.base
import tagopsdb

class Fidelity(tds.apps.base.TDSProgramBase):
    """
    Object to contain all the information for a run.
    """

    def __init__(self, *args, **kwargs):
        # list of with items of form:
        # (deployment, deployed_version, deployed_revision)
        self.bad_deployments = list()
        self.c_dir = kwargs['c_dir'] if 'c_dir' in kwargs else None
        super(Fidelity, self).__init__(*args, **kwargs)
        self.initialize_db()

    def find_bad_deployments(self):
        """
        Find all host deployments that should have been completed according to
        the database but aren't according to the hosts.
        """
        ok_deployments = tds.model.HostDeployment.find(status='ok')
        for dep in ok_deployments:
            print "Getting deployed version, revision for {host}....".format(
                host=dep.host.name
            )
            (dep_version, dep_revision) = self.get_deployed_version_revision(
                dep
            )
            if dep_version != dep.deployment.package.version and \
                dep_revision != dep.deployment.package.revision:
                    self.bad_deployments.append(
                        (dep, dep_version, dep_revision)
                    )

    def get_deployed_version_revision(self, deployment):
        """
        Given a host deployment, find the currently deployed version and
        revision for the application of that deployment on the host of that
        deployment.
        """
        host_name = deployment.host.name
        package_name = deployment.deployment.package.name
        if self.c_dir is not None:
            opts = salt.config.minion_config(
                os.path.join(self.c_dir, 'minion')
            )
        else:
            opts = salt.config.minion_config('/etc/salt.tds/minion')

        caller = salt.client.Caller(mopts=opts)
        host_re = '%s.*' % host_name   # To allow FQDN matching

        # Set timeout high because... RedHat
        result = caller.sminion.functions['publish.full_data'](
            host_re, 'pkg.version', package_name, timeout=30
        )

        print "Result:", result
        if not result:
            return (False, 'No data returned from host %s' % host_name)

        # We're assuming only one key is being returned currently
        host_result = result.values()[0]['ret']
        success = host_result.endswith('successful')

        return (version, revision)
        return (success, host_result)

    def do_run(self):
        self.find_bad_deployments()
        pprint.pprint(self.bad_deployments)

    def correct_hosts(self, hosts, deployments):
        """
        Make the given hosts comply with the database for the given deployments.
        """
        pass

if __name__ == '__main__':
    f = Fidelity(params=dict(user_level='prod'))
    f.do_run()
