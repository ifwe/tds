#  pylint: disable=C0111
import socket
import pprint
import time
import yaml
import sys
import shutil
import random
import contextlib

import os
import os.path
from os.path import dirname, join as opj

from subprocess import CalledProcessError

import tds.authorize
import tds.utils.processes as processes
import tds.utils.merge as merge

sys.path.insert(
    0, opj(os.path.dirname(os.path.realpath(__file__)), 'helpers', 'bin')
)

from hipchat_server import HipChatServer
from graphite_server import GraphiteServer

DB_HOSTS = (
    'dopsdbtds01.tag-dev.com',
    'dopsdbtds02.tag-dev.com',
)

COVERAGE_REPORT_FILENAME = 'coverage.xml'
COVERAGE_DATA_FILENAME = '.coverage'

SMTP_SERVER_PROGRAM = 'smtpd_custom.py'


def before_all(context):
    context.coverage_enabled = True
    context.PROJECT_ROOT = os.path.normpath(opj(dirname(__file__), '..'))

    context.coverage_cmd = lambda c: [
        "coverage",
        c,
        '--rcfile="%s"' % os.path.join(context.PROJECT_ROOT, 'coverage.rc'),
    ]

    processes.run(context.coverage_cmd('erase'), expect_return_code=None)
    for fname in (COVERAGE_REPORT_FILENAME, COVERAGE_DATA_FILENAME):
        fpath = os.path.join(context.PROJECT_ROOT, fname)
        if os.path.isfile(fpath):
            os.remove(fpath)


def after_all(context):
    if not getattr(context, 'coverage_enabled', None):
        return

    processes.run(context.coverage_cmd('combine'), expect_return_code=None)
    processes.run(context.coverage_cmd('xml'), expect_return_code=None)


def setup_workspace(context):
    context.WORK_DIR = opj(context.PROJECT_ROOT, 'work-' + context.unique_id)
    context.AUTH_CONFIG_FILE = opj(context.WORK_DIR, 'auth.yml')
    context.DB_CONFIG_FILE = opj(context.WORK_DIR, 'tagopsdb.yml')
    context.TDS_CONFIG_FILE = opj(context.WORK_DIR, 'deploy.yml')
    context.EMAIL_SERVER_DIR = opj(context.WORK_DIR, 'email-server')
    context.JENKINS_SERVER_DIR = opj(context.WORK_DIR, 'jenkins-server')
    context.REPO_DIR = opj(context.WORK_DIR, 'package-repo')
    context.BIN_DIR = opj(context.PROJECT_ROOT, 'features', 'helpers', 'bin')

    for d in (
        context.WORK_DIR,
        context.REPO_DIR,
        opj(context.REPO_DIR, 'tmp'),
        opj(context.REPO_DIR, 'incoming'),
        opj(context.REPO_DIR, 'builds'),
    ):
        if not os.path.isdir(d):
            os.makedirs(d)


def teardown_workspace(context):
    shutil.rmtree(context.WORK_DIR)


def setup_email_server(context):
    if not os.path.isdir(context.EMAIL_SERVER_DIR):
        os.makedirs(context.EMAIL_SERVER_DIR)

    deploy_info = {}

    with open(context.TDS_CONFIG_FILE) as f_tmpl:
        deploy_info.update(yaml.load(f_tmpl.read()))

    context.tds_email_server_proc = processes.start_process([
        opj(context.BIN_DIR, SMTP_SERVER_PROGRAM),
        deploy_info['notifications']['email']['port'],
    ], cwd=context.EMAIL_SERVER_DIR)


def teardown_email_server(context):
    context.tds_email_server_proc.terminate()
    context.tds_email_server_proc = processes.wait_for_process(
        context.tds_email_server_proc,
        expect_return_code=None
    )

    if 'wip' in context.tags:
        print 'email server stdout:', context.tds_email_server_proc.stdout
        print 'email server stderr:', context.tds_email_server_proc.stderr


def setup_jenkins_server(context):
    if not os.path.isdir(context.JENKINS_SERVER_DIR):
        os.makedirs(context.JENKINS_SERVER_DIR)

    with contextlib.closing(socket.socket()) as sck:
        sck.bind(('', 0))
        port = sck.getsockname()[-1]

    context.tds_jenkins_server_proc = processes.start_process([
        sys.executable,
        '-m',
        'SimpleHTTPServer',
        port,
    ], cwd=context.JENKINS_SERVER_DIR)

    add_config_val(context, 'jenkins', dict(url='http://localhost:%d' % port))
    update_jenkins(
        context,
        'api/python',
        dict(jobs=[])
    )

    context.build_jenkins_url = \
        lambda pth: 'http://localhost:%s/%s' % (port, pth)


def update_jenkins(context, path, data):
    item = opj(context.JENKINS_SERVER_DIR, path)
    item_parent = os.path.dirname(item)

    if not os.path.isdir(item_parent):
        os.makedirs(item_parent)

    old_data = {}
    if os.path.isfile(item):
        with open(item) as f:
            # thar be dragons
            old_data = eval(f.read())

    with open(item, 'wb') as f:
        f.write(repr(merge.merge(old_data, data)))


def teardown_jenkins_server(context):
    context.tds_jenkins_server_proc.terminate()
    context.tds_jenkins_server_proc = processes.wait_for_process(
        context.tds_jenkins_server_proc,
        expect_return_code=None
    )

    if 'wip' in context.tags:
        print 'jenkins stdout:', context.tds_jenkins_server_proc.stdout
        print 'jenkins stderr:', context.tds_jenkins_server_proc.stderr


def setup_hipchat_server(context):
    """
    Set up the mock HipChat server.
    """
    server_name = ''
    server_port = 0

    context.hipchat_server = HipChatServer((server_name, server_port))
    context.hipchat_server.start()

    add_config_val(
        context,
        'notifications.hipchat',
        dict(receiver=context.hipchat_server.address)
    )

def teardown_hipchat_server(context):
    """
    Halt server and print out info if @wip tagged.
    """
    notifications = context.hipchat_server.get_notifications()

    context.hipchat_server.halt()

    if 'wip' in context.tags:
        print 'hipchat notifications:', notifications


def setup_graphite_server(context):
    """
    Set up the mock Graphite server.
    """
    server_name = ''
    server_port = 0

    context.graphite_server = GraphiteServer((server_name, server_port))
    context.graphite_server.start()

    add_config_val(
        context,
        'notifications.graphite',
        dict(host=context.graphite_server.server_address[0],
             port=context.graphite_server.server_address[1],
             prefix=context.graphite_server.prefix),
    )


def teardown_graphite_server(context):
    """
    Tear down the mock Graphite server.
    Print notifications if @wip tagged.
    """
    notifications = context.graphite_server.get_notifications()

    context.graphite_server.halt()

    if 'wip' in context.tags:
        print 'graphite notifications:', notifications


def setup_conf_file(context):
    shutil.copyfile(
        opj(context.PROJECT_ROOT, 'tests',
            'fixtures', 'config', 'deploy.yml'),
        context.TDS_CONFIG_FILE
    )
    shutil.copyfile(
        opj(context.PROJECT_ROOT, 'tests',
            'fixtures', 'config', 'tagopsdb.yml'),
        context.DB_CONFIG_FILE
    )

    auth_levels = tds.authorize.ACCESS_LEVELS

    _conf_dir, filename = os.path.split(context.DB_CONFIG_FILE)
    _basename, ext = os.path.splitext(filename)

    auth_fnames = ['dbaccess.%s%s' % (level, ext) for level in auth_levels]

    for fname in auth_fnames:
        shutil.copyfile(
            opj(context.PROJECT_ROOT, 'tests',
                'fixtures', 'config', 'dbaccess.test.yml'),
            opj(os.path.dirname(context.DB_CONFIG_FILE), fname)
        )

    context.extra_run_args += ['--config-dir', context.WORK_DIR]

    add_config_val(
        context,
        'repo',
        dict(
            build_base=opj(context.REPO_DIR, 'builds'),
            incoming=opj(context.REPO_DIR, 'incoming'),
            processing=opj(context.REPO_DIR, 'processing')
        )
    )

    add_config_val(context, 'mco', dict(bin=opj(context.BIN_DIR, 'mco')))


def add_config_val(context, key, val):
    with open(context.TDS_CONFIG_FILE) as conf_file:
        full_conf = conf = yaml.load(conf_file)

    key_parts = key.split('.')

    for part in key_parts[:-1]:
        conf = conf.setdefault(part, {})

    old_data = conf.get(key_parts[-1], {})
    conf[key_parts[-1]] = merge.merge(old_data, val)

    with open(context.TDS_CONFIG_FILE, 'wb') as conf_file:
        conf_file.write(yaml.dump(full_conf))


def setup_auth_file(context):
    shutil.copyfile(
        opj(context.PROJECT_ROOT, 'tests', 'fixtures', 'config', 'auth.yml'),
        context.AUTH_CONFIG_FILE
    )


def before_scenario(context, scenario):
    context.unique_id = '%s_%d_%d_%d' % (
        get_hex_ip(),
        os.getpid(),
        id(scenario),
        int(time.time()),
    )

    context.extra_run_args = []
    setup_workspace(context)
    setup_auth_file(context)
    setup_conf_file(context)

    if 'jenkins_server' in context.tags:
        setup_jenkins_server(context)

    if 'hipchat_server' in context.tags:
        setup_hipchat_server(context)

    if 'email_server' in context.tags:
        setup_email_server(context)

    if 'graphite_server' in context.tags:
        setup_graphite_server(context)

    setup_temp_db(context)


def after_scenario(context, scenario):
    import tagopsdb
    verbose = scenario.status != 'passed' and 'wip' in context.tags

    if verbose and getattr(context, 'process', None):
        print "subprocess result:"

        if getattr(context.process, 'duration', None) is None:
            print "\twaiting to finish..."
            # process was never finished
            context.process = processes.wait_for_process(
                context.process,
                expect_return_code=None
            )

        print "\tcmd: %r" % context.process.cmd
        print "\tduration: %0.2fs" % context.process.duration
        print "\treturncode: %r" % context.process.returncode
        print "\tstdout: '''%s'''" % context.process.stdout
        print "\tstderr: '''%s'''" % context.process.stderr


    if 'no_db' not in context.tags:
        if verbose:
            print dump_temp_db()

    teardown_temp_db(context)

    if 'email_server' in context.tags:
        teardown_email_server(context)

    if 'jenkins_server' in context.tags:
        teardown_jenkins_server(context)

    if 'hipchat_server' in context.tags:
        teardown_hipchat_server(context)

    if 'graphite_server' in context.tags:
        teardown_graphite_server(context)

    teardown_workspace(context)


def setup_temp_db(context):
    """
    Set up a temporary database for use in the test if 'no_db' is not
    among the tags for the given scenario.
    """
    dry_run = 'no_db' in context.tags
    db_info = {}

    with open(context.DB_CONFIG_FILE) as f_tmpl:
        db_info.update(yaml.load(f_tmpl.read()))

    db_name = 'test_' + context.unique_id

    db_hosts = list(DB_HOSTS)
    random.shuffle(db_hosts)

    if not dry_run:
        exc = None
        while db_hosts:
            db_info['db'].update(
                hostname=db_hosts.pop(0),
                db_name=db_name,
                user='jenkins',
                password='hawaiirobots'
            )

            base_mysql_args = [
                'mysql',
                '--host', db_info['db']['hostname'],
                '--user', db_info['db']['user'],
                '--password=' + db_info['db']['password'],
            ]

            try:
                processes.run(
                    base_mysql_args +
                    [
                        '--execute',
                        'CREATE DATABASE IF NOT EXISTS %s;' % db_name
                    ]
                )
            # Expecting CalledProcessError from tds.process.wait_for_process
            except CalledProcessError as exc:
                # assume it's a host problem
                if db_hosts:
                    exc = None
                    continue
                else:
                    break
            else:
                break

        if exc:
            raise

    auth_levels = tds.authorize.ACCESS_LEVELS

    conf_dir, filename = os.path.split(context.DB_CONFIG_FILE)
    _basename, ext = os.path.splitext(filename)

    auth_fnames = ['dbaccess.%s%s' % (level, ext) for level in auth_levels]

    for fname in [filename] + auth_fnames:
        with open(opj(conf_dir, fname), 'wb') as db_file:
            db_file.write(yaml.dump(db_info))

    if dry_run:
        return

    import tagopsdb
    tagopsdb.init(
        url=dict(
            username=db_info['db']['user'],
            password=db_info['db']['password'],
            host=db_info['db']['hostname'],
            database=db_info['db']['db_name'],
        ),
        pool_recycle=3600,
        create=True,
    )

    seed_db()

    # tagopsdb.Base.metadata.bind.echo = True


def seed_db():
    import tagopsdb
    ganglia = tagopsdb.Ganglia.update_or_create(dict(
        cluster_name='some-ganglia-thing'
    ))

    app_name = tagopsdb.Application.dummy
    tagopsdb.Application.update_or_create(dict(
        app_type=app_name,
        host_base=app_name,
        puppet_class=app_name,
        ganglia_group_name='%s hosts' % app_name,
        description="%s application" % app_name,
        ganglia=ganglia,
    ))

    pkg_name = tagopsdb.PackageDefinition.dummy
    tagopsdb.PackageDefinition.update_or_create(dict(
        deploy_type='rpm',
        validation_type='matching',
        pkg_name=pkg_name,
        path='/some-path',
        build_host='fakeci.example.org',
    ))

    tagopsdb.Session.commit()

def dump_temp_db():
    import tagopsdb
    res = []
    for table_name, table in sorted(
        tagopsdb.Base.metadata.tables.items()
    ):
        result = tagopsdb.Session.query(table).all()
        if len(result) == 0:
            continue

        res.append(table_name.ljust(80, '-'))
        for row in result:
            res.append(pprint.pformat(zip(
                (x.name for x in table.columns),
                row
            )))
        res.append('')

    return '\n'.join(res)


def teardown_temp_db(context):
    dry_run = 'no_db' in context.tags
    if dry_run:
        return

    import tagopsdb
    tagopsdb.destroy()
    sys.modules.pop('tagopsdb', None)


def get_hex_ip():
    ip = socket.gethostbyname_ex(socket.gethostname())[2][0]
    return ''.join('%02X' % int(x) for x in ip.split('.'))
