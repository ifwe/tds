from behave import given, then, when

import os.path
import yaml

import tagopsdb
import tds.model
import tds.commands

def get_model_factory(name):
    if name == 'project':
        return project_factory
    if name == 'deploy target':
        return lambda ctxt, **kwargs: tds.model.AppTarget.create(**kwargs)
    if name == 'package version':
        return package_version_factory
    if name == 'host':
        return host_factory
    if name == 'RPM package':
        return rpm_factory

    return None

def rpm_factory(context, **kwargs):
    name = kwargs.get('name')
    version = kwargs.get('version')
    revision = kwargs.get('revision', 1)
    arch = kwargs.get('arch', 'noarch')
    path = kwargs.get('path')  # see PackageLocation.path

    rpm_name = '%s-%s-%s.%s.rpm' % (name, version, revision, arch)

    full_path = os.path.join(context.REPO_DIR, 'builds', path, rpm_name)
    parent_dir = os.path.dirname(full_path)

    if not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)

    with open(full_path, 'wb') as f:
        f.write(yaml.dump(kwargs))

def host_factory(context, name, **kwargs):

    host = tagopsdb.Host(
        state='operational',
        hostname=name,
        arch='x64',
        kernel_version='2.6.2',
        distribution='Centos 6.4',
        timezone='UTC',
        app_id=tagopsdb.Application.get(name=tagopsdb.Application.dummy).id,
        cage_location=len(tagopsdb.Host.all()),
        cab_location=name[:10],
        section='underdoor',
        rack_location=1,
        console_port='abcdef',
        power_port='ghijkl',
        power_circuit='12345',
        environment_id=tagopsdb.Environment.get(env=context.tds_environment).id,
    )

    tagopsdb.Session.add(host)
    tagopsdb.Session.commit()

    return host

def package_version_factory(context, **kwargs):
    pkg_def = None

    if 'name' in kwargs:
        pkg_def = tagopsdb.PackageDefinition.get(name=kwargs['name'])

    if 'project' in kwargs:
        project = tagopsdb.Project.get(name=kwargs['project'])
    else:
        project = tagopsdb.Project.first()

    if pkg_def is None:
        pkg_def = project.package_definitions[0]

    package = tagopsdb.Package(
        pkg_def_id=pkg_def.id,
        pkg_name=pkg_def.name,
        version=kwargs.get('version', 1),
        revision=kwargs.get('revision', 1),
        status=kwargs.get('status', 'completed'),
        creator='test-user',
        builder='jenkins',
    )

    tagopsdb.Session.add(package)
    tagopsdb.Session.commit()

    return package


def project_factory(context, **kwargs):
    project = tds.model.Project.create(**kwargs)

    tagopsdb.Session.add(tagopsdb.PackageLocation(
        app_name=project.name,
        pkg_name=project.name + '-name',
        pkg_type='jenkins',  # gets mapped into Package.builder
        path=project.name + '-path',
        build_host='',
        environment=False,
    ))

    pkg_def = tagopsdb.PackageDefinition(
        deploy_type='',
        validation_type='',
        pkg_name=project.name + '-name',
        path=project.name + '-path',
        build_host='host with the most',
    )
    tagopsdb.Session.add(pkg_def)

    app = tagopsdb.Application.get(name=tagopsdb.Application.dummy)

    tagopsdb.Session.add(tagopsdb.ProjectPackage(
        project_id=project.id,
        pkg_def_id=pkg_def.id,
        app_id=app.id
    ))

    tagopsdb.Session.commit()
    return project

def parse_properties(properties):
    pairs = [
        (k.strip(), eval(v.strip()))
        for k, v in
        [prop.split('=', 1) for prop in properties.split(',')]
    ]

    attrs = dict()
    for k, v in pairs:
        if k in attrs:
            if not isinstance(attrs[k], list):
                attrs[k] = [attrs[k]]
            attrs[k].append(v)
        else:
            attrs[k] = v

    return attrs

def create_model(context, dest, model_name, properties):
    things = getattr(context, dest, None)
    if things is None:
        things = []
        setattr(context, dest, things)

    attrs = parse_properties(properties)
    model_factory = get_model_factory(model_name)
    if model_factory is None:
        raise Exception("Don't know how to make a %r with properties %r" % (model_name, attrs))

    things.append(model_factory(context, **attrs))

def model_builder(single_string, multiple_string, dest, model_name):
    @given(multiple_string)
    def _handle_multiple(context):
        attr_sets = [dict(zip(context.table.headings, row)) for row in context.table]

        for attr_set in attr_sets:
            context.execute_steps(
                'Given ' + single_string % ','.join('%s="%s"' % i for i in attr_set.items())
            )

    @given(single_string % '{properties}')
    def _handle_single(context, properties):
        create_model(context, dest, model_name, properties)

model_builder(
    'there is a project with %s',
    'there are projects',
    'tds_projects',
    'project',
)

model_builder(
    'there is a host with %s',
    'there are hosts',
    'tds_hosts',
    'host'
)

model_builder(
    'there is a deploy target with %s',
    'there are deploy targets',
    'tds_targets',
    'deploy target'
)

model_builder(
    'there is a package version with %s',
    'there are package versions',
    'tds_package_versions',
    'package version'
)

model_builder(
    'there is an RPM package with %s',
    'there are RPM packages',
    'tds_rpms',
    'RPM package'
)


def add_target_to_project(project, target):
    pkg_def = tagopsdb.PackageDefinition.get(name=project.name + '-name')

    tagopsdb.Session.add(tagopsdb.ProjectPackage(
        project_id=project.id,
        pkg_def_id=pkg_def.id,
        app_id=target.id
    ))
    tagopsdb.Session.commit()


@given(u'the deploy target is a part of the project')
def given_the_deploy_target_is_a_part_of_the_project(context):
    add_target_to_project(context.tds_projects[-1], context.tds_targets[-1])

@given(u'the deploy targets are a part of the project')
def given_the_deploy_targets_are_a_part_of_the_project(context):
    for target in context.tds_targets:
        add_target_to_project(context.tds_projects[-1], target)


def deploy_package_to_target(package, target, env):

    # XXX: fix update_or_create so it can be used here
    dep_props = dict(
        package_id=package.id,
        user='test-user',
        dep_type='deploy',
    )
    dep = tagopsdb.Deployment.get(**dep_props)
    if dep is None:
        dep = tagopsdb.Deployment(**dep_props)

    tagopsdb.Session.add(dep)
    tagopsdb.Session.commit()

    app_dep = tagopsdb.AppDeployment(
        deployment_id=dep.id,
        app_id=target.id,
        user=dep.user,
        status='complete',
        environment_id=tagopsdb.Environment.get(env=env).id,
    )

    tagopsdb.Session.add(app_dep)
    tagopsdb.Session.commit()

@given(u'the package version is deployed on the deploy target')
def given_the_package_version_is_deployed_on_the_deploy_target(context):
    deploy_package_to_target(
        context.tds_package_versions[-1],
        context.tds_targets[-1],
        context.tds_environment,
    )

@given(u'the package version "{version}" is deployed on the deploy target')
def given_the_package_version_is_deployed_on_the_deploy_target(context, version):
    for pkg in context.tds_package_versions:
        if pkg.version == version:
            break
    else:
        pkg = None

    assert pkg is not None
    deploy_package_to_target(
        pkg,
        context.tds_targets[-1],
        context.tds_environment,
    )

@given(u'the package version is deployed on the deploy targets')
def given_the_package_version_is_deployed_on_the_deploy_targets(context):
    for target in context.tds_targets:
        deploy_package_to_target(
            context.tds_package_versions[-1],
            target,
            context.tds_environment,
        )

@given(u'the package version is deployed on the deploy targets in the "{env}" env')
def given_the_package_version_is_deployed_on_the_deploy_targets(context, env):

    if tagopsdb.Environment.get(env=env) is None:
        tagopsdb.Session.add(tagopsdb.Environment(
            env=env,
            environment=tds.commands.DeployController.envs.get(env, env),
            domain=env + 'example.com',
            prefix=env[0]
        ))
        tagopsdb.Session.commit()

    for target in context.tds_targets:
        deploy_package_to_target(
            context.tds_package_versions[-1],
            target,
            env,
        )


@given(u'the package version is deployed on the host with {properties}')
def given_the_package_version_is_deployed_on_host(context, properties):
    attrs = parse_properties(properties)
    package = context.tds_package_versions[-1]

    host = tagopsdb.Host.get(**attrs)
    assert host

    # XXX: fix update_or_create so it can be used here
    dep_props = dict(
        package_id=package.id,
        user='test-user',
        dep_type='deploy',
    )

    deployment = tagopsdb.Deployment.get(**dep_props)
    if deployment is None:
        deployment = tagopsdb.Deployment(**dep_props)
        tagopsdb.Session.add(deployment)
        tagopsdb.Session.commit()

    assert deployment

    host_deployment = tagopsdb.HostDeployment(
        host_id=host.id,
        deployment_id=deployment.id,
        user=deployment.user,
        status='ok',
    )

    tagopsdb.Session.add(host_deployment)
    tagopsdb.Session.commit()

@given(u'the package version is deployed on the hosts')
def given_the_package_version_is_deployed_on_hosts(context):
    for host in context.tds_hosts:
        context.execute_steps('''
            Given the package version is deployed on the host with name="%s"
        ''' % host.name)

@given(u'the package version failed to deploy on the host with {properties}')
def given_the_package_version_failed_to_deploy_on_host(context, properties):
    context.execute_steps('''
        Given the package version is deployed on the host with %s
    ''' % properties)

    attrs = parse_properties(properties)
    package = context.tds_package_versions[-1]

    host = tagopsdb.Host.get(**attrs)
    deployment = tagopsdb.Deployment.get(package_id=package.id)
    host_dep = tagopsdb.HostDeployment.get(
        host_id=host.id, deployment_id=deployment.id
    )

    host_dep.status = 'failed'
    tagopsdb.Session.add(host_dep)
    tagopsdb.Session.commit()

def set_status_for_package_version(package, status):
    print "status:", status, "for package", package
    for deployment in package.deployments:
        print "\tdep", deployment
        for app_dep in deployment.app_deployments:
            app_dep.status = status
            print "\t\tapp_dep", app_dep
            tagopsdb.Session.add(app_dep)

    tagopsdb.Session.commit()

@given(u'the package version is {status}')
def given_the_package_version_is_status(context, status):
    set_status_for_package_version(context.tds_package_versions[-1], status)

@given(u'the package version "{version}" is {status}')
def given_the_package_version_is_validated(context, version, status):
    for package in context.tds_package_versions:
        if package.version == version:
            break
    else:
        package = None


    assert package
    set_status_for_package_version(package, status)


def target_in_project(context):
    project = context.tds_projects[-1]
    target = context.tds_targets[-1]

    return target in project.targets

@then(u'the deploy target is a part of the project')
def then_the_deploy_target_is_a_part_of_the_project(context):
    assert target_in_project(context)

@then(u'the deploy target is not a part of the project')
def then_the_deploy_target_is_not_a_part_of_the_project(context):
    assert not target_in_project(context)

@then(u'the output describes the projects')
def then_the_output_describes_the_projects(context):
    for project in context.tds_projects:
        context.execute_steps('''
            Then the output describes a project with name="%s"
        ''' % project.name)

@then(u'the output describes a project with name="{name}" in a table')
def then_the_output_describes_a_project_with_name_in_a_table(context, name):
    assert ('|-' in context.process.stdout
            or
            '-|' in context.process.stdout)
    pipe_prepended = "| {name}".format(name=name)
    pipe_appended = "{name} |".format(name=name)
    assert (pipe_prepended in context.process.stdout
            or
            pipe_appended in context.process.stdout)

@then(u'the output describes the packages')
def then_the_output_describes_the_packages(context):
    for package in context.tds_package_versions:
        context.execute_steps('''
            Then the output describes a package version with version="%s"
        ''' % package.version)

@then(u'the output describes a package version with {properties}')
def then_the_output_describes_a_project_with_properties(context, properties):
    attrs = parse_properties(properties)
    stdout = context.process.stdout
    stderr = context.process.stderr

    lines = stdout.splitlines()
    processed_attrs = set()

    try:
        if 'version' in attrs:
            assert 'Version: %(version)s' % attrs in lines
            processed_attrs.add('version')
        if 'name' in attrs:
            assert 'Project: %(name)s' % attrs in lines
            processed_attrs.add('name')

        unprocessed_attrs = set(attrs) - processed_attrs
        if unprocessed_attrs:
            assert len(unprocessed_attrs) == 0, unprocessed_attrs

    except AssertionError as e:
        e.args += (stdout, stderr),
        raise e

@then(u'the output describes the packages in a table')
def then_the_output_describes_the_packages_in_a_table(context):
    assert ("|-" in context.process.stdout
            and
            "-|" in context.process.stdout)
    context.execute_steps(u'''
        Then the output is a table with a column containing "{header}"
    '''.format(header="Version"))
    for package in context.tds_package_versions:
        for pkg_attr in (package.version, package.name, package.revision):
            context.execute_steps(u'''
                Then the output is a table with a column containing "{attr}"
            '''.format(attr=pkg_attr))

@then(u'the output is a table with a column containing "{text}"')
def then_the_output_is_a_table_with_a_column_containing(context, text):
    pipe_prepended = '| {text} '.format(text=text)
    pipe_appended = ' {text} |'.format(text=text)
    assert (pipe_prepended in context.process.stdout
            or
            pipe_appended in context.process.stdout)

@then(u'the output describes a project with {properties}')
def then_the_output_describes_a_project_with_properties(context, properties):
    attrs = parse_properties(properties)
    stdout = context.process.stdout
    stderr = context.process.stderr

    lines = stdout.splitlines()
    processed_attrs = set()
    try:
        if 'name' in attrs:
            assert ('Project: %(name)s' % attrs) in lines
            processed_attrs.add('name')

        if 'apptype' in attrs:
            apptypes = attrs['apptype']
            if not isinstance(apptypes, list):
                apptypes = [apptypes]

            for apptype in apptypes:
                assert find_substring_or_regex_in_lines('App types: .*%s.*' % apptype, lines)

            processed_attrs.add('apptype')

        if 'package' in attrs:
            packages = attrs['package']
            if not isinstance(packages, list):
                packages = [packages]

            for package in packages:
                assert ('Application name: %s' % package) in lines

            processed_attrs.add('package')
        unprocessed_attrs = set(attrs) - processed_attrs
        if unprocessed_attrs:
            assert len(unprocessed_attrs) == 0, unprocessed_attrs

    except AssertionError as e:
        e.args += (stdout, stderr),
        raise e

@then(u'the output describes a missing project with {properties}')
def then_the_output_describes_a_missing_project_with_properties(context, properties):
    attrs = parse_properties(properties)

    stdout = context.process.stdout
    stderr = context.process.stderr
    assert ('Project "%(name)s" does not exist' % attrs) in stdout.splitlines(), (stdout, stderr)


def find_substring_or_regex_in_lines(substr, lines):
    import re
    prog = re.compile(substr)

    for line in lines:
        if prog.search(line):
            return True
    else:
        return False


@then(u'the output describes the deployments')
def then_the_output_describes_the_deployments(context):
    project = context.tds_projects[-1]
    package = context.tds_package_versions[-1]

    context.execute_steps('''
        Then the output describes a deployment with name="%s",version="%s"
    ''' % (project.name, package.version))


@then(u'the output describes a deployment with {properties}')
def then_the_output_describes_a_deployment_with_properties(context, properties):
    attrs = parse_properties(properties)
    stdout = context.process.stdout
    stderr = context.process.stderr

    lines = stdout.splitlines()
    processed_attrs = set()
    try:
        if 'name' in attrs:
            assert find_substring_or_regex_in_lines(
                'Deployments? of %(name)s' % attrs, lines
            )
            processed_attrs.add('name')

        if 'version' in attrs:
            assert find_substring_or_regex_in_lines(
                'Version: %(version)s' % attrs, lines
            )
            processed_attrs.add('version')

        unprocessed_attrs = set(attrs) - processed_attrs
        if unprocessed_attrs:
            assert len(unprocessed_attrs) == 0, unprocessed_attrs

    except AssertionError as e:
        e.args += (stdout, stderr),
        raise e


@then(u'the package version is validated')
def then_the_package_is_validated(context):
    package = context.tds_package_versions[-1]
    assert check_package_validation(
        context,
        package,
        package.deployments[-1].app_deployments,
        'validated'
    ), (package.deployments[-1].app_deployments, package.deployments[-1])

@then(u'the package version is invalidated')
def then_the_package_is_invalidated(context):
    package = context.tds_package_versions[-1]
    assert check_package_validation(
        context,
        package,
        package.deployments[-1].app_deployments,
        'invalidated'
    )

@then(u'the package version is validated for deploy target with {properties}')
def then_the_package_is_validated_for_deploy_target(context, properties):
    attrs = parse_properties(properties)
    target = tds.model.AppTarget.get(**attrs)

    # TODO: get only target.app_deployments where package matches.
    assert check_package_validation(
        context,
        context.tds_package_versions[-1],
        [target.app_deployments[-1]],
        'validated'
    )

@then(u'the package version is validated for the deploy targets')
def then_the_package_is_validated_for_the_deploy_targets(context):
    for target in context.tds_targets:
        context.execute_steps('''
            Then the package version is validated for deploy target with name="%s"
        ''' % target.name)


def check_package_validation(context, package, app_deployments, expected_state):
    return all(
        app_dep.status == expected_state
        for app_dep in app_deployments
    )


@then(u'the package version is invalidated for deploy target with {properties}')
def then_the_package_is_invalidated_for_deploy_target(context, properties):
    attrs = parse_properties(properties)
    target = tds.model.AppTarget.get(**attrs)

    # TODO: get only target.app_deployments where package matches.
    assert check_package_validation(
        context,
        context.tds_package_versions[-1],
        [target.app_deployments[-1]],
        'invalidated'
    )


@then(u'there is no project with {properties}')
def then_there_is_no_project_with_properties(context, properties):
    attrs = parse_properties(properties)
    assert tds.model.Project.get(**attrs) is None
    if 'name' in attrs:
        assert tagopsdb.PackageLocation.get(app_name=attrs['name']) is None
        assert tagopsdb.PackageDefinition.get(name=attrs['name']) is None

@then(u'the package version is invalidated for deploy targets')
def then_the_package_is_invalidated_for_deploy_targets(context):
    attr_sets = [
        dict(zip(context.table.headings, row))
        for row in context.table
    ]

    for attr_set in attr_sets:
        context.execute_steps('''
            Then the package version is invalidated for deploy target with name="%(name)s"
        ''' % attr_set)


@then(u'the output describes no deployments')
def then_the_output_describes_no_deployments(context):
    stdout = context.process.stdout
    stderr = context.process.stderr

    assert find_substring_or_regex_in_lines(
        'No deployments to tiers for (.+?) '
        '\\(for possible given version\\) yet in (.+?) environment',
        stdout.splitlines()
    ), ("tiers didn't match", stdout, stderr)
    assert find_substring_or_regex_in_lines(
        'No deployments to hosts for (.+?) '
        '\\(for possible given version\\) in (.+?) environment',
        stdout.splitlines()
    ), ("hosts didn't match", stdout, stderr)


@when('the status is changed to "{status}" for package version with {properties}')
def when_package_version_state_is_changed(context, status, properties):
    attrs = parse_properties(properties)
    pkg = tagopsdb.Package.get(**attrs)
    pkg.status = status
    tagopsdb.Session.add(pkg)
    tagopsdb.Session.commit()


@given(u'the package version has been validated in the "{environment}" environment')
def given_the_package_version_has_been_validated(context, environment):
    targets = context.tds_targets
    package = context.tds_package_versions[-1]
    deployments = tagopsdb.Deployment.find(package_id=package.id)
    dep_ids = [d.id for d in deployments]
    target_ids = [t.id for t in targets]

    for app_dep in tagopsdb.AppDeployment.all():
        if app_dep.deployment_id not in dep_ids:
            continue

        if app_dep.app_id not in target_ids:
            continue

        if app_dep.environment != environment:
            continue

        app_dep.status = 'validated'
        tagopsdb.Session.add(app_dep)

    tagopsdb.Session.commit()


def associate_host_with_target(host, target):
    host.app_id = target.id
    tagopsdb.Session.add(host)
    tagopsdb.Session.commit()

@given(u'the host is associated with the deploy target')
def given_the_host_is_associated_with_the_deploy_target(context):
    associate_host_with_target(context.tds_hosts[-1], context.tds_targets[-1])

@given(u'the hosts are associated with the deploy target')
def given_the_hosts_are_associated_with_the_deploy_target(context):
    target = context.tds_targets[-1]
    hosts = context.tds_hosts

    for host in hosts:
        associate_host_with_target(host, target)
