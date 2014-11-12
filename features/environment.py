#  pylint: disable=C0111
import socket
import operator
import pprint
import time
import yaml
import sys
import shutil
import urlparse
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

def get_fresh_port():
    with contextlib.closing(socket.socket()) as sck:
        sck.bind(('', 0))
        return sck.getsockname()[-1]


class DBDescriptor(dict):
    hostname = property(operator.itemgetter('hostname'))
    port = property(operator.itemgetter('port'))
    user = property(operator.itemgetter('user'))
    password = property(operator.itemgetter('password'))
    db_name = property(operator.itemgetter('db_name'))


class DBProvider(object):
    def create_db(self, db):
        self.mysql_run(db,
            '--execute', "CREATE DATABASE IF NOT EXISTS %s;" % db.db_name
        )

        return db

    def destroy_db(self, db):
        import tagopsdb
        tagopsdb.destroy()
        sys.modules.pop('tagopsdb', None)

    def mysql_run(self, db, *cmd, **kwds):
        cmd = list(cmd)

        return processes.run([
            'mysql',
            '--host=' + db.hostname,
            '--port=' + str(db.port),
            '--user=' + db.user,
            '--password=' + db.password,
        ] + cmd, **kwds)

    def setup(self):
        pass

    def teardown(self):
        pass


class SharedDBProvider(DBProvider):
    user = 'jenkins'
    password = 'hawaiirobots'
    port = 3306

    DB_HOSTS = (
        'dopsdbtds01.tag-dev.com',
        'dopsdbtds02.tag-dev.com',
    )

    def create_db(self, unique_id):
        db_hosts = list(self.DB_HOSTS)
        random.shuffle(db_hosts)

        while self.db_hosts:
            db = DBDescriptor(
                hostname=db_hosts.pop(0),
                port=self.port,
                user=self.user,
                password=self.password,
                db_name='test_' + unique_id,
            )

            try:
                return super(SharedDBProvider, self).create_db(db)
            except CalledProcessError:
                # assume it's a host problem
                if not db_hosts:
                    raise

        return db


class DockerProvider(DBProvider):
    docker_cmd = ['echo']
    user = 'root'
    password = 'journalistsocks'

    def __init__(self, *args):
        super(DockerProvider, self).__init__(*args)
        self._port = None

    def docker(self, *args, **kwargs):
        return processes.run(self.docker_cmd + list(args), **kwargs)

    @property
    def container_id(self):
        return 'behave-%s' % os.getpid()

    def setup(self):
        self.docker(
            'run',
            '-d',
            '-p', '%s:3306' % self.port,
            '--name', self.container_id,
            '--env', "MYSQL_ROOT_PASSWORD=%s" % self.password,
            'mysql',
        )

        proc = None
        print 'Setting up DB container',
        db = self.get_descriptor('test')
        for _ in range(20):
            print '.',
            proc = self.mysql_run(
                db, '--execute', 'SELECT 1;',
                expect_return_code=None
            )

            if proc.returncode == 0:
                break

            time.sleep(2)
        else:
            if not proc or proc.returncode != 0:
                print proc
                raise Exception("Couldn't get database set up")

        print 'done'

        super(DockerProvider, self).setup()

    def get_descriptor(self, unique_id):
        return DBDescriptor(
            hostname=self.hostname,
            port=self.port,
            user=self.user,
            password=self.password,
            db_name='test_' + unique_id,
        )

    def create_db(self, unique_id):
        return super(DockerProvider, self).create_db(self.get_descriptor(unique_id))

    def teardown(self):
        self.docker('stop', self.container_id)
        self.docker('rm', self.container_id)
        super(DockerProvider, self).teardown()

    @property
    def hostname(self):
        return urlparse.urlparse(
            os.environ.get('DOCKER_HOST', '') or 'tcp://127.0.0.1'
        ).netloc.split(':')[0]

    @property
    def port(self):
        if self._port is None:
            self._port = get_fresh_port()

        return self._port


class MacDockerProvider(DockerProvider):
    docker_cmd = ['docker']

class LinuxDockerProvider(DockerProvider):
    docker_cmd = ['sudo'] + MacDockerProvider.docker_cmd

def db_provider_type():
    if processes.run('boot2docker', expect_return_code=None).returncode == 0:
        return MacDockerProvider()

    if processes.run('docker', expect_return_code=None).returncode == 0:
        return LinuxDockerProvider()

    return SharedDBProvider()


COVERAGE_REPORT_FILENAME = 'coverage.xml'
COVERAGE_DATA_FILENAME = '.coverage'

SMTP_SERVER_PROGRAM = 'smtpd_custom.py'


def before_all(context):
    setup_db_provider(context)

    context.coverage_enabled = True
    context.PROJECT_ROOT = os.path.normpath(opj(dirname(__file__), '..'))

    processes.run('coverage erase', expect_return_code=None)
    for fname in (COVERAGE_REPORT_FILENAME, COVERAGE_DATA_FILENAME):
        fpath = os.path.join(context.PROJECT_ROOT, fname)
        if os.path.isfile(fpath):
            os.remove(fpath)


def after_all(context):
    if not getattr(context, 'coverage_enabled', None):
        return

    processes.run('coverage combine', expect_return_code=None)
    processes.run('coverage xml', expect_return_code=None)

    teardown_db_provider(context)


def setup_workspace(context):
    context.WORK_DIR = opj(context.PROJECT_ROOT, 'work-' + context.unique_id)
    context.AUTH_CONFIG_FILE = opj(context.WORK_DIR, 'auth.yml')
    context.DB_CONFIG_FILE = opj(context.WORK_DIR, 'tagopsdb.yml')
    context.TDS_CONFIG_FILE = opj(context.WORK_DIR, 'deploy.yml')
    context.EMAIL_SERVER_DIR = opj(context.WORK_DIR, 'email-server')
    context.JENKINS_SERVER_DIR = opj(context.WORK_DIR, 'jenkins-server')
    context.HIPCHAT_SERVER_DIR = opj(context.WORK_DIR, 'hipchat-server')
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

    port = get_fresh_port()

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

    context.hipchat_server = HipChatServer(
        (server_name, server_port),
        opj(context.HIPCHAT_SERVER_DIR, 'notifications.txt'),
    )
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

    setup_temp_db(context)


def after_scenario(context, scenario):
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

    teardown_workspace(context)


def setup_db_provider(context):
    context.db_provider = db_provider_type()
    context.db_provider.setup()


def teardown_db_provider(context):
    context.db_provider.teardown()


def setup_temp_db(context):
    """
    Set up a temporary database for use in the test if 'no_db' is not
    among the tags for the given scenario.
    """
    dry_run = 'no_db' in context.tags
    db_info = {}

    with open(context.DB_CONFIG_FILE) as f_tmpl:
        db_info.update(yaml.load(f_tmpl.read()))

    if not dry_run:
        try:
            context.db = context.db_provider.create_db(context.unique_id)
        except CalledProcessError as exc:
            print >>sys.stderr, exc
            print exc.stdout
            print exc.stderr
            raise

        db_info['db'].update(context.db)

        import tagopsdb
        tagopsdb.init(
            url=dict(
                username=context.db.user,
                password=context.db.password,
                host=context.db.hostname,
                port=context.db.port,
                database=context.db.db_name,
            ),
            pool_recycle=3600,
            create=True,
        )

        seed_db()

    auth_levels = tds.authorize.ACCESS_LEVELS

    conf_dir, filename = os.path.split(context.DB_CONFIG_FILE)
    _basename, ext = os.path.splitext(filename)

    auth_fnames = ['dbaccess.%s%s' % (level, ext) for level in auth_levels]

    for fname in [filename] + auth_fnames:
        with open(opj(conf_dir, fname), 'wb') as db_file:
            db_file.write(yaml.dump(db_info))


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

    context.db_provider.destroy_db(context.db)

def get_hex_ip():
    ip = socket.gethostbyname_ex(socket.gethostname())[2][0]
    return ''.join('%02X' % int(x) for x in ip.split('.'))
