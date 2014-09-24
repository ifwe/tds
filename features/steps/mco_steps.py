import collections
import os.path
import json

import tagopsdb
import tds.model
import tds.utils.merge as merge

from .model_steps import parse_properties

from behave import then

INPUT_FILE = 'mco-input.json'
RESULTS_FILE = 'mco-results.json'


def load_mco_data(context):
    results_file = os.path.join(context.WORK_DIR, RESULTS_FILE)

    if not os.path.isfile(results_file):
        return []

    with open(results_file) as f:
        data = f.read()
        return json.loads(data)


def set_mco_input(context, info):
    input_file = os.path.join(context.WORK_DIR, INPUT_FILE)

    old_data = {}

    if os.path.isfile(input_file):
        with open(input_file) as f:
            old_data = json.loads(f.read())

    data = merge.merge(old_data, info)

    with open(input_file, 'wb') as f:
        f.write(json.dumps(data))


@then(u'package "{pkg}" version "{version}" was deployed to host "{hostname}"')
def then_the_package_version_was_deployed_to_host(context, pkg, version, hostname):
    mco_data = load_mco_data(context)

    package = tagopsdb.Package.get(name=pkg, version=version)
    assert package is not None, (pkg, version)

    hosts_to_packages = collections.defaultdict(list)
    for info in mco_data:
        hosts_to_packages[info['hostname']].append(info)

    names_versions = [
        (package_info['package'], package_info['version'])
        for package_info in hosts_to_packages[hostname]
    ]

    assert (package.name, package.version) in names_versions, mco_data

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
def then_the_package_version_was_deployed_to_these_hosts(context, pkg, version):
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
def then_the_package_version_was_deployed_to_deploy_target(context, pkg, version):
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
def then_package_was_restarted_on_a_specific_deploy_target(context, pkg, version, properties):
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
def then_the_package_version_was_deployed_to_deploy_target(context, pkg, version):
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
def then_package_was_restart_on_host(context, pkg, hostname):
    mco_data = load_mco_data(context)

    package = tagopsdb.Package.get(name=pkg)
    assert package is not None, pkg

    hosts_to_packages = collections.defaultdict(list)
    for info in mco_data:
        hosts_to_packages[info['hostname']].append(info)

    names_restarts = [
        (package_info['package'], package_info['restart'])
        for package_info in hosts_to_packages[hostname]
    ]

    assert (package.name, True) in names_restarts, mco_data

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
def then_package_was_restarted_on_a_specific_deploy_target(context, pkg, properties):
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
def then_package_was_restarted_on_host(context, pkg):
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
    set_mco_input(context, {
        hostname: {
            'hostname': hostname,
            'exitcode': 1,
            'stderr': 'its broken!'
        }
    })
