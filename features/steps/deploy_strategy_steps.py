# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""salt configuration and management for feature tests"""

import os.path
import json

import tagopsdb
import tds.model
import tds.utils.merge as merge

from .model_steps import parse_properties
from .environment import add_config_val

from behave import given, then

class DeployStrategyHelper(object):
    INPUT_FILE = None
    RESULTS_FILE = None

    def __init__(self, context):
        self.context = context

    def get_info_for_host(self, hostname, transform=None):
        if transform is None:
            transform = lambda x: x

        return [
            transform(package_info)
            for package_info in self.load_results()
            if package_info['hostname'] == hostname
        ]

    def get_deployments_for_host(self, hostname):
        return self.get_info_for_host(
            hostname,
            lambda x: (x['package'], x['version'])
        )

    def get_restarts_for_host(self, hostname):
        return self.get_info_for_host(
            hostname,
            lambda x: (x['package'], x['restart'])
        )

    def _load_json(self, fname, default=None):
        if not os.path.isfile(fname):
            return default

        with open(fname) as fobj:
            return json.load(fobj)

    def load_results(self):
        return self._load_json(
            os.path.join(self.context.WORK_DIR, self.RESULTS_FILE),
            []
        )

    def load_input(self):
        return self._load_json(
            os.path.join(self.context.WORK_DIR, self.INPUT_FILE),
            []
        )

    def set_input(self, info):
        input_file = os.path.join(self.context.WORK_DIR, self.INPUT_FILE)
        old_data = self._load_json(input_file, {})

        data = merge.merge(old_data, info)

        with open(input_file, 'wb') as fobj:
            json.dump(data, fobj)


class SaltHelper(DeployStrategyHelper):
    INPUT_FILE = 'salt-input.json'
    RESULTS_FILE = 'salt-results.json'


def set_strat_helper(context, strategy):
    assert strategy in ('salt'), "invalid helper: %s" % strategy

    context.strategy_helper_type = strategy
    add_config_val(context, 'deploy_strategy', strategy)

def get_strat_helper(context):
    helper = context.strategy_helper_type
    assert helper in ('salt'), "invalid helper: %s" % helper

    if helper == 'salt':
        return SaltHelper(context)


given(u'the deploy strategy is "{strategy}"')(set_strat_helper)

@then(u'package "{pkg}" version "{version}" was deployed to host "{hostname}"')
def then_the_package_version_was_deployed_to_host(context, pkg, version,
                                                  hostname):

    package = tagopsdb.Package.get(name=pkg, version=version)
    assert package is not None, (pkg, version)
    assert (
        (package.name, package.version) in
        get_strat_helper(context).get_deployments_for_host(hostname)
    )


@then(u'package "{pkg}" version "{version}" was not deployed to host "{hostname}"')
def then_package_was_not_deployed_to_the_host(context, pkg, version, hostname):
    package = tagopsdb.Package.get(name=pkg, version=version)
    assert package is not None, (pkg, version)
    assert (
        (package.name, package.version) not in
        get_strat_helper(context).get_deployments_for_host(hostname)
    )


def check_restart_on_hosts(context, hosts, pkg):
    ran_steps = False
    for host in hosts:
        context.execute_steps('''
            Then package "%s" was restarted on host "%s"
        ''' % (pkg, host.name))
        ran_steps = True
    return ran_steps


def check_deployment_on_hosts(context, hostnames, pkg, version):
    ran_steps = False
    for hostname in hostnames:
        context.execute_steps('''
            Then package "%s" version "%s" was deployed to host "%s"
        ''' % (pkg, version, hostname))
        ran_steps = True

    return ran_steps


@then(u'package "{pkg}" version "{version}" was deployed to the hosts')
def then_package_version_was_deployed_to_hosts(context, pkg, version):
    assert check_deployment_on_hosts(
        context,
        [
            x.hostname for x in context.tds_hosts
            if x.environment_obj.env == context.tds_env
        ],
        pkg,
        version
    )


@then(u'package "{pkg}" version "{version}" was deployed to these hosts')
def then_the_package_version_was_deployed_to_these_hosts(context, pkg,
                                                         version):
    attr_sets = [
        dict(zip(context.table.headings, row))
        for row in context.table
    ]

    assert check_deployment_on_hosts(
        context,
        [x['name'] for x in attr_sets],
        pkg,
        version
    )


@then(u'package "{pkg}" version "{version}" was deployed to the deploy target')
def then_the_package_version_was_deployed_to_deploy_target(context, pkg,
                                                           version):
    assert check_deployment_on_hosts(
        context,
        [
            x.hostname
            for x in context.tds_targets[-1].hosts
            if x.environment_obj.env == context.tds_env
        ],
        pkg,
        version
    )


@then(u'package "{pkg}" version "{version}" was deployed to the deploy target with {properties}')
def then_package_version_was_restarted_on_a_specific_deploy_target(
        context, pkg, version, properties
):
    attrs = parse_properties(properties)
    targets = tds.model.AppTarget.find(**attrs)

    assert check_deployment_on_hosts(
        context,
        [
            x.hostname
            for target in targets
            for x in target.hosts
            if x.environment_obj.env == context.tds_env
        ],
        pkg,
        version
    )


@then(u'package "{pkg}" version "{version}" was deployed to the deploy targets')
def then_the_package_version_was_deployed_to_deploy_targets(context, pkg,
                                                            version):
    assert check_deployment_on_hosts(
        context,
        [
            x.hostname
            for target in context.tds_targets
            for x in target.hosts
            if x.environment_obj.env == context.tds_env
        ],
        pkg,
        version
    )


@then(u'package "{pkg}" was restarted on host "{hostname}"')
def then_package_was_restarted_on_host(context, pkg, hostname):
    package = tagopsdb.Package.get(name=pkg)
    assert package is not None, pkg

    assert (
        (package.name, True) in
        get_strat_helper(context).get_restarts_for_host(hostname)
    )


def check_restart_on_targets(context, targets, pkg):
    return check_restart_on_hosts(
        context,
        [
            x
            for target in targets
            for x in target.hosts
            if x.environment_obj.env == context.tds_env
        ],
        pkg
    )


@then(u'package "{pkg}" was restarted on the deploy target with {properties}')
def then_package_was_restarted_on_a_specific_deploy_target(context, pkg,
                                                           properties):
    attrs = parse_properties(properties)
    targets = tds.model.AppTarget.find(**attrs)
    assert check_restart_on_targets(context, targets, pkg)


@then(u'package "{pkg}" was restarted on the deploy target')
def then_package_was_restarted_on_deploy_target(context, pkg):
    assert check_restart_on_targets(context, [context.tds_targets[-1]], pkg)


@then(u'package "{pkg}" was restarted on the deploy targets')
def then_package_was_restarted_on_deploy_targets(context, pkg):
    assert check_restart_on_targets(context, context.tds_targets, pkg)


@then(u'package "{pkg}" was restarted on the host')
def then_package_was_restarted_on_the_host(context, pkg):
    assert check_restart_on_hosts(context, [context.tds_hosts[-1]], pkg)


@then(u'package "{pkg}" was restarted on the hosts')
def then_package_was_restarted_on_hosts(context, pkg):
    assert check_restart_on_hosts(context, context.tds_hosts, pkg)


@then(u'package "{pkg}" was restarted on the host with {properties}')
def then_package_was_restarted_on_host_with_properties(context, pkg, properties):
    attrs = parse_properties(properties)
    hosts = tagopsdb.Host.find(**attrs)
    assert check_restart_on_hosts(context, hosts, pkg)


@given(u'the host "{hostname}" will fail to {action}')
def given_the_host_will_fail_to_deploy(context, hostname, action):

    get_strat_helper(context).set_input({
        hostname: {
            'hostname': hostname,
            'exitcode': 1,
            'stderr': 'It done broked!',
            'result': 'It done broked!',
        }
    })


@then(u'there were no deployments run')
def then_there_were_no_deployments_run(context):
    helper = get_strat_helper(context)
    results = helper.load_results()
    inp = helper.load_input()
    assert not (results or inp), (results, inp)
