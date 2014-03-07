import subprocess
import json
import re

import tds.utils

from .base import DeployStrategy


class TDSMCODeployStrategy(DeployStrategy):
    @tds.utils.debug
    def process_mco_command(self, mco_cmd, retry):
        """Run a given MCollective 'mco' command"""

        self.log.debug('Running MCollective command')
        self.log.debug(5, 'Command is: %s' % ' '.join(mco_cmd))

        proc = subprocess.Popen(
            mco_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate()

        if proc.returncode:
            return (False, 'The mco process failed to run successfully.\n'
                           'return code is %r.\n'
                           'Stdout: %r\n'
                           'Stderr: %r' % (proc.returncode, stdout, stderr))

        mc_output = None
        summary = None

        # Extract the JSON output and summary line
        for line in stdout.split('\n'):
            if not line:
                continue

            if line.startswith('{'):
                mc_output = json.loads(line)

            if line.startswith('Finished'):
                summary = line.strip()

        # Ensure valid response and extract information
        if mc_output is None or summary is None:
            return (False, 'No output or summary information returned '
                           'from mco process')

        self.log.debug(summary)
        m = re.search(r'processing (\d+) / (\d+) ', summary)

        if m is None:
            return (False, 'Error parsing summary line.')

        # Virtual hosts in dev tend to time out unpredictably, probably
        # because vmware is slow to respond when the hosts are not
        # active. Subsequent retries after a timeout work better.
        if m.group(2) == '0' and retry > 0:
            self.log.debug('Discovery failure, trying again.')
            return self.process_mco_command(mco_cmd, retry-1)

        for host, hostinfo in mc_output.iteritems():
            if hostinfo['exitcode'] != 0:
                return (False, hostinfo['stderr'].strip())
            else:
                return (True, 'Deploy successful')

        return (False, 'Unknown/unparseable mcollective output: %s' %
                stdout)

    @tds.utils.debug
    def restart_host(self, dep_host, app, retry=4):
        """Restart application on a given host"""

        self.log.debug('Restarting application on host %r', dep_host)

        mco_cmd = ['/usr/bin/mco', 'tds', '--discovery-timeout', '4',
                   '--timeout', '60', '-W', 'hostname=%s' % dep_host,
                   app, 'restart']

        return self.process_mco_command(mco_cmd, retry)

    @tds.utils.debug
    def deploy_to_host(self, dep_host, app, version, retry=4):
        self.log.debug('Deploying to host %r' % dep_host)

        mco_cmd = ['/usr/bin/mco', 'tds', '--discovery-timeout', '4',
                   '--timeout', '60', '-W', 'hostname=%s' % dep_host,
                   app, version]

        return self.process_mco_command(mco_cmd, retry)
