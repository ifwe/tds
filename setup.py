from setuptools import setup
from setuptools.command.test import test as TestCommand

import sys

# Let's add this later
# long_description = open('README.txt').read()

# Get version of project
import tds.version


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = [self.test_suite]

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        if errno != 0:
            raise SystemExit("Test failures (errno=%d)", errno)


PYTHON27_REQ_BLACKLIST = ['argparse', 'ordereddict']


def load_requirements(fname):
    requirements = []
    with open(fname, 'r') as reqfile:
        reqs = reqfile.read()

    for req in filter(None, reqs.strip().splitlines()):
        if req.startswith('git+'):
            req = '=='.join(req.rsplit('=')[-1].rsplit('-', 1))
        if sys.version_info > (2, 7) or sys.version_info > (3, 2):
            if any(req.startswith(bl) for bl in PYTHON27_REQ_BLACKLIST):
                continue
        requirements.append(req)

    return requirements

REQUIREMENTS = load_requirements('requirements.txt')
DEV_REQUIREMENTS = load_requirements('requirements-dev.txt')

setup_args = dict(
    name='TDS',
    version=tds.version.__version__,
    description='Tagged Deployment System',
    # long_description = long_description,
    author='Kenneth Lareau',
    author_email='klareau@tagged.com',
    license='MIT',
    packages=[
        'tds',
        'tds.deploy_strategy',
        'tds.notifications',
        'tds.scripts',
        'tds.commands',
        'tds.utils'
    ],
    install_requires=REQUIREMENTS,
    entry_points={
        'console_scripts': [
            'tds = tds.scripts.tds_prog:main',
            'tds_install = tds.scripts.tds_install:main',
            'unvalidated_deploy_check = tds.scripts.unvalidated_deploy_check:main',
            'update_deploy_repo = tds.scripts.update_deploy_repo:daemon_main',
        ]
    },
    data_files = [
        ('share/tds/salt', ['share/tds_cmd.py']),
    ],
    test_suite='tests',
    tests_require=REQUIREMENTS + DEV_REQUIREMENTS,
    cmdclass=dict(test=PyTest)
)

if __name__ == '__main__':
    setup(**setup_args)
