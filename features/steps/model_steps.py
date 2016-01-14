"""Model configuration/management for feature tests"""

import itertools
import os.path
import json
import yaml
from time import mktime

from behave import given, then, when

import tagopsdb
import tds.model
import tds.commands
import tds.exceptions


def get_model_factory(name):
    if name == 'project':
        return project_factory
    if name == 'deploy target':
        return tier_factory
    if name == 'package':
        return package_factory
    if name == 'host':
        return host_factory
    if name == 'RPM package':
        return rpm_factory
    if name == 'application':
        return application_factory

    return None


def tier_factory(context, **kwargs):
    if kwargs.get('distribution', None) is None:
        kwargs['distribution'] = 'centos6.5'
    return tds.model.AppTarget.create(**kwargs)


def rpm_factory(context, **kwargs):
    name = kwargs.get('name')
    version = kwargs.get('version')
    release = kwargs.get('release', 1)
    arch = kwargs.get('arch', 'noarch')

    # path = kwargs.get('path')  # see PackageLocation.path

    rpm_name = '%s-%s-%s.%s.rpm' % (name, version, release, arch)

    dest_directory = kwargs.get('directory', 'incoming')
    full_path = os.path.join(context.REPO_DIR, dest_directory, rpm_name)
    parent_dir = os.path.dirname(full_path)

    if not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)

    with open(full_path, 'wb') as f:
        f.write(yaml.dump(kwargs))


def host_factory(context, name, env=None, **kwargs):
    env = env or context.tds_env
    env_obj = tagopsdb.Environment.get(env=env)
    assert env_obj is not None
    env_id = env_obj.id

    host = tagopsdb.Host(
        state=kwargs.get('state', 'operational'),
        hostname=name,
        distribution=kwargs.get('distribution', 'Centos 6.4'),
        app_id=kwargs.get(
            'app_id',
            tagopsdb.Application.get(name=tagopsdb.Application.dummy).id
        ),
        cage_location=len(tagopsdb.Host.all()),
        cab_location=name[:10],
        rack_location=1,
        console_port='abcdef',
        environment_id=env_id,
    )

    tagopsdb.Session.add(host)
    tagopsdb.Session.commit()

    return host


def package_factory(context, **kwargs):
    pkg_def = None

    if 'name' in kwargs:
        application = tds.model.Application.get(name=kwargs['name'])
    elif hasattr(context, 'tds_applications'):
        application = context.tds_applications[-1]
    else:
        if 'project' in kwargs:
            project = tds.model.Project.get(name=kwargs['project'])
        else:
            project = context.tds_projects[-1]

        if len(project.applications) > 0:
            application = project.applications[0]
        else:
            # TODO: Make this work, the application_factory will barf a
            # "Column 'pkg_name' cannot be null" error when trying to insert
            # into table package_definitions.
            application = application_factory(context)

    package = tagopsdb.Package(
        pkg_def_id=application.id,
        pkg_name=application.name,
        version=kwargs.get('version', 1),
        revision=kwargs.get('revision', 1),
        status=kwargs.get('status', 'completed'),
        creator='test-user',
        builder='jenkins',
        job=kwargs.get('job', application.path),
    )

    tagopsdb.Session.add(package)
    tagopsdb.Session.commit()

    return package


def application_factory(context, **kwargs):
    # TODO: This will fail if there is no pkg_name entry in kwargs,
    # since package_definitions requires it to be non-Null.
    fields = dict(
        deploy_type='rpm',
        validation_type='matching',
        path=kwargs.get('job', 'job'),
        arch='noarch',
        build_type='jenkins',
        build_host='fakeci.example.org',
    )
    fields.update(kwargs)
    application = tds.model.Application.create(**fields)

    tagopsdb.Session.add(application)
    tagopsdb.Session.commit()
    return application


def project_factory(context, **kwargs):
    project = tds.model.Project.create(**kwargs)

    # NOTE: the commented out code below will need to be handled
    # in other factories
    #
    #application = tds.model.Application.get(name=tds.model.Application.dummy)
    #
    #pkg_name = tagopsdb.PackageName(
    #    name=application.pkg_name,
    #    pkg_def_id=application.id,
    #)
    #tagopsdb.Session.add(pkg_name)
    #
    #target = tds.model.AppTarget.get(name=tds.model.AppTarget.dummy)
    #
    #tagopsdb.Session.add(tagopsdb.ProjectPackage(
    #    project_id=project.id,
    #    pkg_def_id=application.id,
    #    app_id=target.id
    #))

    tagopsdb.Session.commit()
    return project


def parse_properties(properties):
    """
    Return a dictionary of attributes based on properties.
    Convert properties of form "property1=value1,property2=value2, ..."
    to {'property1': value1, 'property2': value2, ...}.
    """
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
        raise tds.exceptions.TDSException(
            "Don't know how to make a %r with properties %r"
            % (model_name, attrs)
        )

    things.append(model_factory(context, **attrs))


def model_builder(single_string, multiple_string, dest, model_name):
    @given(multiple_string)
    def _handle_multiple(context):
        attr_sets = [
            dict(zip(context.table.headings, row)) for row in context.table
        ]

        for attr_set in attr_sets:
            context.execute_steps(
                'Given ' + single_string % ','.join(
                    ['%s="%s"' % i for i in attr_set.items()]
                )
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
    'there is a package with %s',
    'there are packages',
    'tds_packages',
    'package'
)

model_builder(
    'there is an RPM package with %s',
    'there are RPM packages',
    'tds_rpms',
    'RPM package'
)

model_builder(
    'there is an application with %s',
    'there are applications',
    'tds_applications',
    'application'
)


def add_target_to_proj_app(project, application, target):
    tagopsdb.Session.add(tagopsdb.ProjectPackage(
        project_id=project.id,
        pkg_def_id=application.id,
        app_id=target.id
    ))
    tagopsdb.Session.commit()


@given(u'the deploy target is a part of the project-application pair')
def given_the_deploy_target_is_a_part_of_the_proj_app_pair(context):
    add_target_to_proj_app(
        context.tds_projects[-1],
        context.tds_applications[-1],
        context.tds_targets[-1]
    )


@given(u'the deploy targets are a part of the project-application pair')
def given_the_deploy_targets_are_a_part_of_the_proj_app_pair(context):
    for target in context.tds_targets:
        add_target_to_proj_app(
            context.tds_projects[-1],
            context.tds_applications[-1],
            target
        )


@given(u'the deploy targets are a part of the project-application pairs')
def given_the_deploy_targets_are_a_part_of_the_proj_app_pairs(context):
    for project in context.tds_projects:
        for application in context.tds_applications:
            for target in context.tds_targets:
                add_target_to_proj_app(
                    project,
                    application,
                    target
                )


def deploy_package_to_target(package, target, env, status='complete',
                             dep_status='pending'):
    env_id = tagopsdb.Environment.get(env=env).id

    # XXX: fix update_or_create so it can be used here
    dep_props = dict(
        user='test-user',
        status=dep_status,
    )
    dep = tagopsdb.Deployment.get(**dep_props)
    if dep is None:
        dep = tagopsdb.Deployment(**dep_props)

    tagopsdb.Session.add(dep)
    tagopsdb.Session.commit()

    app_dep = tagopsdb.AppDeployment(
        package_id=package.id,
        deployment_id=dep.id,
        app_id=target.id,
        user=dep.user,
        status=status,
        environment_id=env_id,
    )

    tagopsdb.Session.add(app_dep)
    tagopsdb.Session.commit()

    deploy_to_hosts(
        tagopsdb.Host.find(app_id=target.id, environment_id=env_id),
        dep,
        package.id,
    )


def deploy_to_hosts(hosts, deployment, package_id, status='ok'):
    """
    Add a host deployment entry for the given package to every host in hosts,
    using the given deployment.
    """
    for host in hosts:
        if tagopsdb.HostDeployment.get(deployment_id=deployment.id,
                                       host_id=host.id) is None:
            host_dep = tagopsdb.HostDeployment(
                deployment_id=deployment.id,
                host_id=host.id,
                user='test-user',
                status=status,
                package_id=package_id,
            )

            tagopsdb.Session.add(host_dep)
            tagopsdb.Session.commit()


@given(u'the package is deployed on the deploy target')
def given_the_package_is_deployed_on_the_deploy_target(context):
    deploy_package_to_target(
        context.tds_packages[-1],
        context.tds_targets[-1],
        context.tds_env,
    )


def check_if_package_exists(context, version):
    for pkg in context.tds_packages:
        if pkg.version == version:
            break
    else:
        pkg = None

    assert pkg is not None
    return pkg


@given(u'the package "{version}" is deployed on the deploy target')
def given_the_package_specific_is_deployed_on_the_deploy_target(
        context, version
):
    pkg = check_if_package_exists(context, version)

    deploy_package_to_target(
        pkg,
        context.tds_targets[-1],
        context.tds_env,
    )


@given(u'the package is deployed on the deploy targets')
def given_the_package_is_deployed_on_the_deploy_targets(context):
    for target in context.tds_targets:
        deploy_package_to_target(
            context.tds_packages[-1],
            target,
            context.tds_env,
        )


@given(u'the package is deployed on the deploy targets in the "{env}" env')
def given_the_package_is_deployed_on_the_deploy_targets_in_env(
        context, env
):
    env_obj = tagopsdb.Environment.get(env=env)
    assert env_obj is not None

    for target in context.tds_targets:
        deploy_package_to_target(
            context.tds_packages[-1],
            target,
            env_obj.env,
        )

@given(u'the package "{version}" is deployed on the deploy targets in the "{env}" env')
def given_the_package_specific_is_deployed_on_the_deploy_targets_in_env(
        context, version, env
):
    pkg = check_if_package_exists(context, version)

    env_obj = tagopsdb.Environment.get(env=env)
    assert env_obj is not None

    for target in context.tds_targets:
        deploy_package_to_target(
            pkg,
            target,
            env_obj.env,
        )


@given(u'the package is deployed on the host with {properties}')
def given_the_package_is_deployed_on_host(context, properties):
    attrs = parse_properties(properties)
    package = context.tds_packages[-1]

    host = tagopsdb.Host.get(**attrs)
    assert host

    if tagopsdb.HostDeployment.get(host_id=host.id) is not None:
        tagopsdb.Session.delete(
            tagopsdb.HostDeployment.get(host_id=host.id)
        )
        tagopsdb.Session.commit()

    # XXX: fix update_or_create so it can be used here
    dep_props = dict(
        user='test-user',
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
        package_id=package.id,
    )

    tagopsdb.Session.add(host_deployment)
    tagopsdb.Session.commit()


@given(u'the package is deployed on the hosts')
def given_the_package_is_deployed_on_hosts(context):
    for host in context.tds_hosts:
        context.execute_steps('''
            Given the package is deployed on the host with name="%s"
        ''' % host.name)


@given(u'the package failed to deploy on the host with {properties}')
def given_the_package_failed_to_deploy_on_host(context, properties):
    attrs = parse_properties(properties)
    package = context.tds_packages[-1]

    host = tagopsdb.Host.get(**attrs)

    host_dep = tagopsdb.HostDeployment.get(
        host_id=host.id, package_id=package.id
    )

    host_dep.status = 'failed'
    tagopsdb.Session.add(host_dep)
    tagopsdb.Session.commit()

    given_the_package_has_status_set_with_properties(
        context,
        package.version,
        context.tds_environment,
        'incomplete'
    )

def set_status_for_package(package, status):
    for app_dep in package.app_deployments:
        app_dep.status = status
        tagopsdb.Session.add(app_dep)

    tagopsdb.Session.commit()


@given(u'the package is {status}')
def given_the_package_is_status(context, status):
    set_status_for_package(context.tds_packages[-1], status)


@given(u'the package "{version}" is {status}')
def given_the_package_is_validated(context, version, status):
    for package in context.tds_packages:
        if package.version == version:
            break
    else:
        package = None

    assert package
    set_status_for_package(package, status)


def target_in_project(context):
    project = context.tds_projects[-1]
    target = context.tds_targets[-1]

    return target in project.targets


def target_in_project_application(context, target):
    project = context.tds_projects[-1]
    application = context.tds_applications[-1]

    return target in project.targets and target in application.targets


@then(u'the deploy target is a part of the project-application pair')
def then_the_deploy_target_is_a_part_of_the_proj_app_pair(context):
    target = context.tds_targets[-1]
    assert target_in_project_application(context, target)


@then(u'the deploy targets are a part of the project-application pair')
def then_the_deploy_targets_are_a_part_of_the_proj_app_pair(context):
    for target in context.tds_targets:
        assert target_in_project_application(context, target)


@then(u'the deploy target is not a part of the project-application pair')
def then_the_deploy_target_is_not_a_part_of_the_proj_app_pair(context):
    target = context.tds_targets[-1]
    assert not target_in_project_application(context, target)


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
    pipe_prepended = "| {name} ".format(name=name)
    pipe_appended = " {name} |".format(name=name)
    assert (pipe_prepended in context.process.stdout
            or
            pipe_appended in context.process.stdout)


@then(u'the output describes a project with name="{name}" in json')
def then_the_output_describes_a_project_with_name_in_json(context, name):
    try:
        actual = json.loads(context.process.stdout)
    except ValueError as exc:
        exc.args += (context.process.stdout, context.process.stderr)
        raise exc

    expected = dict(id=1, name=name)
    for k in expected:
        assert expected[k] == actual[0][k]


@then(u'the output describes a project with name="{name}" in latex')
def then_the_output_describes_a_project_with_name_in_latex(context, name):
    expected = (
        '\\begin{tabular}{l}',
        '\hline',
        ' Project   \\\\',
        ' {name}{spaces}\\\\'.format(
            name=name, spaces=" " * (10 - len(name))
        ),
        '\end{tabular}',
    )
    output_lines = context.process.stdout.splitlines()
    for line in expected:
        assert line in output_lines


@then(u'the output describes a project with name="{name}" in rst')
def then_the_output_describes_a_project_with_name_in_rst(context, name):
    expected = (
        "=========",
        "Project",
        name,
    )
    output_lines = context.process.stdout.splitlines()
    for line in expected:
        assert line in output_lines


@then(u'there is an application')
def then_there_is_an_application(context):
    attrs = {}
    for row in context.table:
        key, value = row
        attrs[key] = value

    app = tds.model.Application.get(**attrs)

    assert app is not None


@then(u'there is an application with {properties}')
def then_there_is_an_application_with_properties(context, properties):
    attrs = parse_properties(properties)
    app = tds.model.Application.get(**attrs)

    assert app is not None


@then(u'the output describes the applications')
def then_the_output_describes_the_applications(context):
    for application in context.tds_applications:
        context.execute_steps('''
            Then the output describes an application with name="%s",deploy_type="%s",arch="%s",build_type="%s",build_host="%s",path="%s"
        ''' % (application.name, application.deploy_type, application.arch,
               application.build_type, application.build_host,
               application.path))


@then(u'the output describes an application with {properties}')
def then_the_output_describes_an_application_with_properties(context, properties):
    attrs = parse_properties(properties)
    stdout = context.process.stdout
    stderr = context.process.stderr

    lines = stdout.splitlines()
    processed_attrs = set()
    try:
        if 'name' in attrs:
            assert ('Application: %(name)s' % attrs) in lines
            processed_attrs.add('name')

        if 'deploy_type' in attrs:
            assert ('Deploy type: %(deploy_type)s' % attrs) in lines
            processed_attrs.add('deploy_type')

        if 'arch' in attrs:
            assert ('Architecture: %(arch)s' % attrs) in lines
            processed_attrs.add('arch')

        if 'build_type' in attrs:
            assert ('Build system type: %(build_type)s' % attrs) in lines
            processed_attrs.add('build_type')

        if 'build_host' in attrs:
            assert ('Build host: %(build_host)s' % attrs) in lines
            processed_attrs.add('build_host')

        if 'path' in attrs:
            assert ('Path: %(path)s' % attrs) in lines
            processed_attrs.add('path')

        unprocessed_attrs = set(attrs) - processed_attrs
        if unprocessed_attrs:
            assert len(unprocessed_attrs) == 0, unprocessed_attrs

    except AssertionError as exc:
        exc.args += (stdout, stderr),
        raise exc


@then(u'the output describes a missing application with {properties}')
def then_the_output_describes_a_missing_application_with_properties(
        context, properties
):
    attrs = parse_properties(properties)

    stdout = context.process.stdout
    stderr = context.process.stderr
    names = attrs['name'] if isinstance(attrs['name'], list) else [attrs['name']]
    assert 'Application%s do%s not exist: %s' % (
        '' if len(names) == 1 else 's',
        'es' if len(names) == 1 else '',
        ', '.join(names)
    ) in stdout.splitlines(), (stdout, stderr)


@then(u'the output describes an application in {output_format} with name="{name}"')
def then_the_output_describes_an_application_with_name_in_format(
        context, output_format, name
):
    lines = context.process.stdout.splitlines()
    if output_format == 'json':
        try:
            actual = json.loads(context.process.stdout)
        except ValueError as exc:
            exc.args += (context.process.stdout, context.process.stderr)
            raise exc

        expected = tds.model.Application.get(name=name).to_dict()
        for k in expected:
            print "%s, %s" % (expected[k], actual[-1][k])
            if k == 'created':
                expected[k] = int(mktime(expected[k].timetuple()))
            assert expected[k] == actual[-1][k]
    elif output_format in ('table', 'a table'):
        assert any(['| Application' in line for line in lines])
        assert any(['|---' in line for line in lines])
        assert any(['---|' in line for line in lines])
        assert any(['| {name} '.format(name=name) in line for line in lines])
    elif output_format == 'rst':
        expected = "=============\nApplication\n=============\napp1\n=============\n"
        assert context.process.stdout == expected
    elif output_format == 'latex':
        expected = "\\begin{tabular}{l}\n\\hline\n Application   \\\\\n\\hline\n app1          \\\\\n\hline\n\\end{tabular}\n"
        assert context.process.stdout == expected
    else:
        context.stdout += "\n\nUnrecognized output format: %s" % output_format
        assert False


@then(u'the output describes the packages')
def then_the_output_describes_the_packages(context):
    for package in context.tds_packages:
        context.execute_steps('''
            Then the output describes a package with version="%s"
        ''' % package.version)


@then(u'the output describes a package with {properties}')
def then_the_output_describes_a_package_with_properties(context, properties):
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

    except AssertionError as exc:
        exc.args += (stdout, stderr),
        raise exc


def isa_group_separator(line):
    return line == '\n'


def package_match(attrs, lines):
    processed_attrs = set()

    try:
        if 'name' in attrs:
            assert 'Project: %(name)s' % attrs in lines
            processed_attrs.add('name')
        if 'version' in attrs:
            assert 'Version: %(version)s' % attrs in lines
            processed_attrs.add('version')

        unprocessed_attrs = set(attrs) - processed_attrs
        if unprocessed_attrs:
            assert len(unprocessed_attrs) == 0, unprocessed_attrs

    except AssertionError:
        return False
    else:
        return True


@then(u'the output does not describe a package with {properties}')
def then_the_output_does_not_describe_a_package_with_properties(context, properties):
    attrs = parse_properties(properties)
    stdout = context.process.stdout
    stderr = context.process.stderr

    for sep, line_group in itertools.groupby(stdout, isa_group_separator):
        if sep:
            continue

        lines = ''.join([x for x in line_group]).splitlines()
        assert not package_match(attrs, lines), (stdout, stderr)


@then(u'the output describes the packages in a table')
def then_the_output_describes_the_packages_in_a_table(context):
    assert ("|-" in context.process.stdout
            and
            "-|" in context.process.stdout)
    for header in ('Project', 'Version', 'Revision'):
        context.execute_steps(u'''
            Then the output is a table with a column containing "{header}"
        '''.format(header=header))
    for package in context.tds_packages:
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


@then(u'the output describes the packages in json')
def then_the_output_describes_the_packages_in_json(context):
    try:
        actual = json.loads(context.process.stdout)
    except ValueError as exc:
        exc.args += (context.process.stdout, context.process.stderr)
        raise exc

    for package in context.tds_packages:
        expected = dict(id=package.id,
                        pkg_name=package.name,
                        version=package.version)
        for k in expected:
            assert expected[k] == actual[int(package.version)-1][k]


@then(u'the output describes the packages in latex')
def then_the_output_describes_the_packages_in_latex(context):
    output_lines = context.process.stdout.splitlines()
    for package in context.tds_packages:
        expected = (
            '\\begin{tabular}{lrr}',
            '\hline',
            ' Project   &   Version &   Revision \\\\',
            ' {package.name}{s1}&{s2}{package.version}'
            ' &{s3}{package.revision} \\\\'.format(
                package=package,
                s1=" " * (10 - len(package.name)),
                s2=" " * (10 - len(package.version)),
                s3=" " * (11 - len(package.revision)),
            ),
            '\end{tabular}',
        )
        for line in expected:
            assert line in output_lines


@then(u'the output describes the packages in rst')
def then_the_output_describes_the_packages_in_rst(context):
    output_lines = context.process.stdout.splitlines()
    for package in context.tds_packages:
        expected = (
            "=========  =========  ==========",
            "Project      Version    Revision",
            "{package.name}{s1}{package.version}"
            "{s2}{package.revision}".format(
                package=package,
                s1=" " * (20 - len(package.name) - len(package.version)),
                s2=" " * (12 - len(package.revision)),
            ),
        )
        for line in expected:
            assert line in output_lines


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
                assert find_substring_or_regex_in_lines('App types: .*%s.*'
                                                        % apptype, lines)

            processed_attrs.add('apptype')

        if 'arch' in attrs:
            arch = attrs['arch']
            assert find_substring_or_regex_in_lines(
                'Architecture: {arch}'.format(arch=arch), lines
            )

            processed_attrs.add('arch')

        if 'path' in attrs:
            path = attrs['path']
            assert find_substring_or_regex_in_lines(
                'Path: {path}'.format(path=path), lines
            )

            processed_attrs.add('path')

        if 'host' in attrs:
            host = attrs['host']
            assert find_substring_or_regex_in_lines(
                'Build host: {host}'.format(host=host), lines
            )

            processed_attrs.add('host')

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

    except AssertionError as exc:
        exc.args += (stdout, stderr),
        raise exc


@then(u'the output describes the host deployments')
def then_the_output_describes_the_host_deployments(context):
    package = context.tds_packages[-1]

    for host in context.tds_hosts:
        context.execute_steps('''
            Then the output describes a host deployment with host_name="%s",name="%s"
        ''' % (host.name, package.name))


@then(u'the output describes a host deployment with {properties}')
def then_the_output_describes_a_host_deployment_with_properties(context,
                                                                properties):
    attrs = parse_properties(properties)
    stdout = context.process.stdout
    stderr = context.process.stderr

    lines = stdout.splitlines()
    processed_attrs = set()
    try:
        if 'name' in attrs:
            assert find_substring_or_regex_in_lines(
                'Deployments? of %(name)s to hosts in .* environment'
                % attrs, lines
            )
            processed_attrs.add('name')

        if 'host_name' in attrs:
            assert find_substring_or_regex_in_lines(
                'Hostname: %(host_name)s' % attrs, lines
            )
            processed_attrs.add('host_name')

        unprocessed_attrs = set(attrs) - processed_attrs
        if unprocessed_attrs:
            assert len(unprocessed_attrs) == 0, unprocessed_attrs

    except AssertionError as exc:
        exc.args += (stdout, stderr),
        raise exc


@then(u'the output does not describe a host deployment with {properties}')
def then_the_output_does_not_describe_a_host_with_properties(context,
                                                             properties):
    attrs = parse_properties(properties)
    stdout = context.process.stdout
    stderr = context.process.stderr

    lines = stdout.splitlines()
    processed_attrs = set()
    try:
        if 'name' in attrs:
            assert not find_substring_or_regex_in_lines(
                'Deployments? of %(name)s to hosts in .* environment'
                % attrs, lines
            )
            processed_attrs.add('name')

        if 'host_name' in attrs:
            assert not find_substring_or_regex_in_lines(
                'Hostname: %(host_name)s' % attrs, lines
            )
            processed_attrs.add('host_name')

        unprocessed_attrs = set(attrs) - processed_attrs
        if unprocessed_attrs:
            assert len(unprocessed_attrs) == 0, unprocessed_attrs

    except AssertionError as exc:
        exc.args += (stdout, stderr),
        raise exc


@then(u'the output describes a missing project with {properties}')
def then_the_output_describes_a_missing_project_with_properties(context,
                                                                properties):
    attrs = parse_properties(properties)

    stdout = context.process.stdout
    stderr = context.process.stderr
    names = attrs['name'] if isinstance(attrs['name'], list) else [attrs['name']]

    if len(names) == 1:
        message = 'Project does not exist: %s'
    else:
        message = 'Projects do not exist: %s'

    assert message % ', '.join(names) \
        in stdout.splitlines(), (stdout, stderr)


def find_substring_or_regex_in_lines(substr, lines):
    """Return True iff substr can be found in any line of lines."""

    import re
    prog = re.compile(substr)

    return any(prog.search(line) for line in lines)


@then(u'the output describes the app deployments')
def then_the_output_describes_the_app_deployments(context):
    package = context.tds_packages[-1]

    context.execute_steps('''
        Then the output describes an app deployment with name="%s",version="%s",declaring_user="%s"
    ''' % (package.name, package.version, package.creator))


@then(u'the output describes an app deployment with {properties}')
def then_the_output_describes_an_app_deployment_with_properties(context,
                                                                properties):
    attrs = parse_properties(properties)
    stdout = context.process.stdout
    stderr = context.process.stderr

    lines = stdout.splitlines()
    processed_attrs = set()

    try:
        if 'name' in attrs:
            assert find_substring_or_regex_in_lines(
                'Deployments? of %(name)s to [^ ]* tier in [^ ]* environment'
                % attrs, lines
            )
            processed_attrs.add('name')

        if 'version' in attrs:
            assert find_substring_or_regex_in_lines(
                'Version: %(version)s' % attrs, lines
            )
            processed_attrs.add('version')

        if 'declaring_user' in attrs:
            assert find_substring_or_regex_in_lines(
                'Declaring user: %(declaring_user)s' % attrs, lines
            )
            processed_attrs.add('declaring_user')

        if 'realizing_user' in attrs:
            assert find_substring_or_regex_in_lines(
                'Realizing_user: %(realizing_user)s' % attrs, lines
            )
            processed_attrs.add('realizing_user')

        if 'install_state' in attrs:
            assert find_substring_or_regex_in_lines(
                'Install state: %(install_state)s' % attrs, lines
            )
            processed_attrs.add('install_state')

        unprocessed_attrs = set(attrs) - processed_attrs
        if unprocessed_attrs:
            assert len(unprocessed_attrs) == 0, unprocessed_attrs

    except AssertionError as exc:
        exc.args += (stdout, stderr),
        raise exc


@then(u'the output does not describe an app deployment with {properties}')
def then_the_output_does_not_describe_an_app_deployment_with_properties(
        context, properties
):
    attrs = parse_properties(properties)
    stdout = context.process.stdout
    stderr = context.process.stderr

    lines = stdout.splitlines()
    processed_attrs = set()

    try:
        if 'name' in attrs:
            assert not find_substring_or_regex_in_lines(
                'Deployments? of %(name)s to [^ ]* tier in [^ ]* environment'
                % attrs, lines
            )
            processed_attrs.add('name')

        if 'version' in attrs:
            assert not find_substring_or_regex_in_lines(
                'Version: %(version)s' % attrs, lines
            )
            processed_attrs.add('version')

        if 'declaring_user' in attrs:
            assert not find_substring_or_regex_in_lines(
                'Declaring user: %(declaring_user)s' % attrs, lines
            )
            processed_attrs.add('declaring_user')

        if 'realizing_user' in attrs:
            assert not find_substring_or_regex_in_lines(
                'Realizing_user: %(realizing_user)s' % attrs, lines
            )
            processed_attrs.add('realizing_user')

        if 'install_state' in attrs:
            assert not find_substring_or_regex_in_lines(
                'Install state: %(install_state)s' % attrs, lines
            )
            processed_attrs.add('install_state')

        unprocessed_attrs = set(attrs) - processed_attrs
        if unprocessed_attrs:
            assert len(unprocessed_attrs) == 0, unprocessed_attrs

    except AssertionError as exc:
        exc.args += (stdout, stderr),
        raise exc


@then(u'the package is validated')
def then_the_package_is_validated(context):
    package = context.tds_packages[-1]
    assert check_package_validation(
        context,
        package,
        package.app_deployments,
        'validated'
    ), (package.deployments[-1].app_deployments, package.deployments[-1])


@then(u'the package is invalidated')
def then_the_package_is_invalidated(context):
    package = context.tds_packages[-1]
    assert check_package_validation(
        context,
        package,
        package.deployments[-1].app_deployments,
        'invalidated'
    )


@then(u'the package version "{version}" is invalidated')
def then_the_package_version_is_invalidated(context, version):
    package = check_if_package_exists(context, version)
    assert check_package_validation(
        context,
        package,
        package.app_deployments,
        'invalidated'
    )


@then(u'the package is validated for deploy target with {properties}')
def then_the_package_is_validated_for_deploy_target(context, properties):
    attrs = parse_properties(properties)
    target = tds.model.AppTarget.get(**attrs)

    # TODO: get only target.app_deployments where package matches.
    assert check_package_validation(
        context,
        context.tds_packages[-1],
        [target.app_deployments[-1]],
        'validated'
    )


@then(u'the package is validated for the deploy targets')
def then_the_package_is_validated_for_the_deploy_targets(context):
    for target in context.tds_targets:
        context.execute_steps('''
            Then the package is validated for deploy target with name="%s"
        ''' % target.name)


def check_package_validation(context, package, app_deployments,
                             expected_state):
    # XXX: Should the package parameter be used at all?
    return all(
        app_dep.status == expected_state
        for app_dep in app_deployments
    )


@then(u'the package is invalidated for deploy target with {properties}')
def then_the_package_is_invalidated_for_deploy_target(context, properties):
    attrs = parse_properties(properties)
    target = tds.model.AppTarget.get(**attrs)

    # TODO: get only target.app_deployments where package matches.
    assert check_package_validation(
        context,
        context.tds_packages[-1],
        [target.app_deployments[-1]],
        'invalidated'
    )


def check_if_app_deployment_exists(context, package, app_deployments):
    for app_deployment in app_deployments:
        if app_deployment.package == package:
            break
    else:
        app_deployment = None

    assert app_deployment is not None
    return app_deployment


@then(u'the package version "{version}" is invalidated for deploy target with {properties}')
def then_the_package_is_invalidated_for_deploy_target(context, version, properties):
    package = check_if_package_exists(context, version)
    attrs = parse_properties(properties)
    target = tds.model.AppTarget.get(**attrs)
    app_deployment = check_if_app_deployment_exists(
        context, package, target.app_deployments
    )

    # TODO: get only target.app_deployments where package matches.
    assert check_package_validation(
        context,
        package,
        [app_deployment],
        'invalidated'
    )


@then(u'there is no project with {properties}')
def then_there_is_no_project_with_properties(context, properties):
    attrs = parse_properties(properties)
    assert tds.model.Project.get(**attrs) is None
    if 'name' in attrs:
        assert tagopsdb.PackageLocation.get(name='%s-name' % attrs['name']) is None
        assert tagopsdb.PackageDefinition.get(name='%s-name' % attrs['name']) is None


@then(u'the package is invalidated for deploy targets')
def then_the_package_is_invalidated_for_deploy_targets(context):
    attr_sets = [
        dict(zip(context.table.headings, row))
        for row in context.table
    ]

    for attr_set in attr_sets:
        context.execute_steps('''
            Then the package is invalidated for deploy target with name="%s"
        ''' % attr_set['name'])



@then(u'the package version "{version}" is invalidated for deploy targets')
def then_the_package_is_invalidated_for_deploy_targets(context, version):
    attr_sets = [
        dict(zip(context.table.headings, row))
        for row in context.table
    ]

    for attr_set in attr_sets:
        context.execute_steps('''
            Then the package version "%s" is invalidated for deploy target with name="%s"
        ''' % (version, attr_set['name']))


@then(u'the output describes no deployments')
def then_the_output_describes_no_deployments(context):
    stdout = context.process.stdout
    stderr = context.process.stderr

    assert find_substring_or_regex_in_lines(
        'No deployments to tiers for (.+?) '
        '\\(for possible given version\\) yet in (.+?) environment',
        stdout.splitlines()
    ), ("tiers didn't match", stdout, stderr)


@when('the status is changed to "{status}" for package with {properties}')
def when_package_state_is_changed(context, status, properties):
    tagopsdb.Session.close()
    attrs = parse_properties(properties)
    pkg = tds.model.Package.get(**attrs)
    pkg.status = status
    tagopsdb.Session.add(pkg.delegate)
    tagopsdb.Session.commit()


def given_the_package_has_status_set_with_properties(
        context, version, environment, status
):
    targets = context.tds_targets
    package = context.tds_packages[-1] if version is None \
        else check_if_package_exists(context, version)
    target_ids = [t.id for t in targets]

    for app_dep in tagopsdb.AppDeployment.find(package_id=package.id):
        if app_dep.app_id not in target_ids:
            continue
        if app_dep.environment != environment:
            continue
        app_dep.status = status
        tagopsdb.Session.add(app_dep)

    if status in ('validated', 'invalidated'):
        for host_dep in tagopsdb.HostDeployment.find(package_id=package.id):
            if host_dep.host.environment != environment:
                continue
            tagopsdb.Session.delete(host_dep)

    tagopsdb.Session.commit()


@given(u'the package has been validated in the "{environment}" environment')
def given_the_package_has_been_validated_with_properties(context,
                                                         environment):
    given_the_package_has_status_set_with_properties(
        context, None, environment, 'validated'
    )


@given(u'the package "{version}" has been validated in the "{environment}" environment')
def given_the_package_specific_has_been_validated_with_properties(
        context, version, environment
):
    given_the_package_has_status_set_with_properties(
        context, version, environment, 'validated'
    )


@given(u'the package has been invalidated in the "{environment}" environment')
def given_the_package_has_been_invalidated_with_properties(context,
                                                           environment):
    given_the_package_has_status_set_with_properties(
        context, None, environment, 'invalidated'
    )


@given(u'the package "{version}" has been invalidated in the "{environment}" environment')
def given_the_package_specific_has_been_invalidated_with_properties(
        context, version, environment
):
    given_the_package_has_status_set_with_properties(
        context, version, environment, 'invalidated'
    )


@given(u'the package has been validated')
def given_the_package_has_been_validated(context):
    context.execute_steps('''
        Given the package has been validated in the "%s" environment
    ''' % context.tds_environment)


@given(u'the package has been invalidated')
def given_the_package_has_been_invalidated(context):
    context.execute_steps('''
        Given the package has been invalidated in the "%s" environment
    ''' % context.tds_environment)


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


@given(u'the package with {package_props} is deployed on the deploy target with {target_props}')
def given_the_package_is_deployed_on_the_target(context, package_props, target_props):
    package_attrs = parse_properties(package_props)
    target_attrs = parse_properties(target_props)

    package = tagopsdb.Package.get(**package_attrs)
    target = tds.model.AppTarget.get(**target_attrs)

    assert package is not None, package_attrs
    assert target is not None, target_attrs

    deploy_package_to_target(package, target, context.tds_env)


@given(u'there is an ongoing deployment on the hosts="{hosts}"')
def give_there_is_an_ongoing_deployment_on_the_hosts(context, hosts):
    host_names = hosts.split(',')

    package_id = context.tds_packages[-1].id

    dep_props = dict(
        user='test-user',
    )

    deployment = tagopsdb.Deployment.get(**dep_props)
    if deployment is None:
        deployment = tagopsdb.Deployment(**dep_props)
        deployment.status = 'inprogress'
        tagopsdb.Session.add(deployment)
        tagopsdb.Session.commit()

    hosts = [tagopsdb.Host.get(hostname=host_name)
             for host_name in host_names]

    deploy_to_hosts(hosts, deployment, package_id, 'inprogress')


@given(u'there is an ongoing deployment on the deploy target')
def given_there_is_an_ongoing_deployment_on_the_deploy_target(context):
    deploy_package_to_target(
        context.tds_packages[-1],
        context.tds_targets[-1],
        context.tds_env,
        'inprogress',
        'inprogress',
    )


@given(u'make will return {value}')
def given_make_will_return(context, value):
    value_list = value.split(',')
    value_dict = dict()
    for num, val in enumerate(value_list, 1):
        value_dict['exit_code_{v}'.format(v=num)] = int(val)

    json_file = os.path.join(context.WORK_DIR, 'make-behavior.json')
    with open(json_file, 'w') as f:
        json.dump(value_dict, f)


@given(u'a file with name "{pkg_name}" is in the "{dir_name}" directory')
def given_a_package_with_name_is_in_the_directoary(context, pkg_name, dir_name):
    dir_name = os.path.join(context.REPO_DIR, dir_name)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)
    file_name = os.path.join(dir_name, pkg_name)
    with open(file_name, 'w+') as f:
        f.write('')


@then(u'the "{dir_name}" directory is empty')
def then_the_directory_is_empty(context, dir_name):
    dir_name = os.path.join(context.REPO_DIR, dir_name)
    assert os.path.isdir(dir_name)
    assert not os.listdir(dir_name), os.listdir(dir_name)


@then(u'the RPM with name {properties} is not in the "{dir_name}" directory')
def the_package_with_name_is_removed_from_the_directory(context, properties, dir_name):
    dir_name = os.path.join(context.REPO_DIR, dir_name)
    rpm_name = '{name}-{version}-{revision}.{arch}.rpm'.format(
        parse_properties(properties)
    )
    file_name = os.path.join(dir_name, rpm_name)
    assert os.path.isdir(dir_name)
    assert not any(name == rpm_name for name in os.listdir(dir_name))
    assert not os.path.isfile(file_name) , "{file_name} should not exist".format(
        file_name=file_name
    )


@then('the package status is "{status}"')
def then_the_package_status_is(context, status):
    assert context.tds_packages[-1].status == status, (context.tds_packages[-1].status,
                                                       status)


@then(u'the update repo log file has "{text}"')
def then_update_repo_log_file_has(context, text):
    with open(os.path.join(context.WORK_DIR, 'update_deploy_repo.log')) as fh:
        actual = fh.read()
        assert text in actual, (text, actual)


@given(u'there is a Ganglia with {properties}')
def given_there_is_a_ganglia_with(context, properties):
    properties = parse_properties(properties)
    created = tagopsdb.model.Ganglia.update_or_create(properties)
    tagopsdb.Session.commit()


@given(u'there is a HipChat with {properties}')
def given_there_is_a_hipchat_with(context, properties):
    properties = parse_properties(properties)
    created = tagopsdb.model.Hipchat.update_or_create(properties)
    tagopsdb.Session.commit()


@given(u'there are hipchat rooms')
def given_there_are_hipchat_rooms(context):
    hipchats = getattr(context, 'hipchats', list())
    for row in context.table:
        hipchat = tagopsdb.Hipchat(
            room_name=row['room_name'],
        )
        hipchats.append(hipchat)
        tagopsdb.Session.add(hipchat)
    tagopsdb.Session.commit()
    context.hipchats = hipchats


@given(u'the deploy target "{targ}" is associated with the hipchat "{room}"')
def given_the_deploy_target_is_associated_with_the_hipchat(context, targ,
                                                           room):
    hipchat = tagopsdb.Hipchat.get(room_name=room)
    target = tagopsdb.AppDefinition.get(name=targ)
    if hipchat is None:
        assert False, "HipChat %s doesn't exist" % room
    if target is None:
        assert False, "Target %s doesn't exist" % targ
    if target not in hipchat.app_definitions:
        hipchat.app_definitions.append(target)
    tagopsdb.Session.commit()


def targ_room_associated(targ, room):
    """
    Return true if the application type with name targ is associated with the
    HipChat room with name room, false otherwise.
    Raise exception if either targ or room doesn't resolve to a tier or
    HipChat room, respectively
    """
    hipchat = tagopsdb.Hipchat.get(room_name=room)
    target = tagopsdb.AppDefinition.get(name=targ)
    if hipchat is None:
        assert False, "HipChat %s doesn't exist" % room
    if target is None:
        assert False, "Target %s doesn't exist" % targ
    return target in hipchat.app_definitions


@then(u'the deploy target "{targ}" is associated with the hipchat "{room}"')
def then_the_deploy_target_is_associated_with_the_hipchat(context, targ,
                                                          room):
    assert targ_room_associated(targ, room)


@then(u'the deploy target "{targ}" is not associated with the hipchat "{room}"')
def then_the_deploy_target_is_not_associated_with_the_hipchat(context, targ,
                                                              room):
    assert not targ_room_associated(targ, room)


@given(u'there are deployments')
def given_there_are_deployments(context):
    deployments = getattr(context, 'deployments', list())
    for row in context.table:
        attrs = dict()
        for heading in context.table.headings:
            attrs[heading] = row[heading]
        deployment = tagopsdb.Deployment(**attrs)
        tagopsdb.Session.add(deployment)
        deployments.append(deployment)
    tagopsdb.Session.commit()
    context.deployments = deployments


NAME_OBJ_MAPPINGS = {
    'application': tds.model.Application,
    'package': tds.model.Package,
    'deploy target': tds.model.AppTarget,
    'host': tds.model.HostTarget,
    'tier': tds.model.AppTarget,
    'deployment': tds.model.Deployment,
    'host deployment': tds.model.HostDeployment,
    'tier deployment': tds.model.AppDeployment,
    'ganglia': tagopsdb.model.Ganglia,
    'hipchat': tagopsdb.model.Hipchat,
    'project': tds.model.Project,
    'environment': tagopsdb.model.Environment,
    'project-package': tagopsdb.model.ProjectPackage,
}


@then(u'there is a {model} with {properties}')
def then_there_is_a_model_with(context, model, properties):
    model = NAME_OBJ_MAPPINGS[model.lower()]
    tagopsdb.Session.close()
    properties = parse_properties(properties)
    found = model.get(**properties)
    assert found is not None, (found, model.all())


@then(u'there is an {obj_type} with {properties}')
def then_there_is_an_obj_type_with(context, obj_type, properties):
    model = NAME_OBJ_MAPPINGS[obj_type.lower()]
    tagopsdb.Session.close()
    properties = parse_properties(properties)
    found = model.get(**properties)
    assert found is not None, (found, model.all())


@then(u'there is no {model} with {properties}')
def then_there_is_no_model_with(context, model, properties):
    model = NAME_OBJ_MAPPINGS[model.lower()]
    tagopsdb.Session.close()
    properties = parse_properties(properties)
    found = model.get(**properties)
    assert found is None, found


@given(u'there are host deployments')
def given_there_are_host_deployments(context):
    host_deps = getattr(context, 'host_deployments', list())
    for row in context.table:
        attrs = dict()
        for heading in context.table.headings:
            attrs[heading] = row[heading]
        dep = tagopsdb.HostDeployment(**attrs)
        tagopsdb.Session.add(dep)
        host_deps.append(dep)
    tagopsdb.Session.commit()
    context.host_deployments = host_deps


@given(u'there are tier deployments')
def given_there_are_tier_deployments(context):
    tier_deps = getattr(context, 'host_deployments', list())
    for row in context.table:
        attrs = dict()
        for heading in context.table.headings:
            attrs[heading] = row[heading]
        dep = tagopsdb.AppDeployment(**attrs)
        tagopsdb.Session.add(dep)
        tier_deps.append(dep)
    tagopsdb.Session.commit()
    context.host_deployments = tier_deps


@given(u'the tier "{tier}" is associated with the application "{app}" for the project "{proj}"')
def given_the_tier_is_associated_with_the_application_for_the_project(
    context, tier, app, proj
):
    found_tier = tds.model.AppTarget.get(name=tier)
    found_app = tds.model.Application.get(name=app)
    found_proj = tds.model.Project.get(name=proj)
    assert None not in (found_tier, found_app, found_proj), (
        found_tier, found_app, found_proj,
    )
    proj_pkg = tagopsdb.model.ProjectPackage(
        project_id=found_proj.id,
        pkg_def_id=found_app.id,
        app_id=found_tier.id,
    )
    tagopsdb.Session.add(proj_pkg)
    tagopsdb.Session.commit()

@when(u'the status of the {obj_type} with {props} changes to "{status}"')
def when_the_status_of_deployment_changes_to(context, obj_type, props, status):
    properties = parse_properties(props)
    obj_mapping = {
        'deployment': tagopsdb.model.Deployment,
        'host deployment': tagopsdb.model.HostDeployment,
        'tier deployment': tagopsdb.model.AppDeployment,
        'package': tagopsdb.model.Package,
    }
    assert obj_type in obj_mapping

    model = obj_mapping[obj_type]
    tagopsdb.Session.close()
    instance = model.get(**properties)
    assert instance is not None

    instance.status = status
    tagopsdb.Session.commit()
