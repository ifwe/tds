from setuptools import setup
from setuptools.command.test import test as TestCommand

import sys
import os, os.path
import fnmatch

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


def discover_packages(base):
    '''
    Discovers all sub-packages for a base package
    Note: does not work with namespaced packages (via pkg_resources or similar)
    '''
    import importlib
    mod = importlib.import_module(base)
    mod_fname = mod.__file__
    mod_dirname = os.path.normpath(os.path.dirname(mod_fname))

    for root, _dirnames, filenames in os.walk(mod_dirname):
        for _fname in fnmatch.filter(filenames, '__init__.py'):
            yield '.'.join(os.path.relpath(root).split(os.sep))


REQ_BLACKLIST = ['tagopsdb']

if sys.version_info > (2, 7) or sys.version_info > (3, 2):
    REQ_BLACKLIST.extend(['argparse', 'ordereddict'])

def reqfile_read(fname):
    with open(fname, 'r') as reqfile:
        reqs = reqfile.read()

    return filter(None, reqs.strip().splitlines())


def load_requirements(fname):
    requirements = []

    for req in reqfile_read(fname):
        if 'git+' in req:
            req = '>='.join(req.rsplit('=')[-1].split('-', 3)[:2])
        if any(req.startswith(bl) for bl in REQ_BLACKLIST):
            continue
        if req.startswith('--'):
            continue
        requirements.append(req)

    return requirements

REQUIREMENTS = {}
REQUIREMENTS['install'] = load_requirements('requirements.txt')
REQUIREMENTS['install'].append('tagopsdb>0.9.0')
REQUIREMENTS['tests'] = load_requirements('requirements-dev.txt')

def load_github_dependency_links(fname):
    dep_links = []
    for req in reqfile_read(fname):
        if 'git+' in req and 'github' in req:  # not exactly precise...
            url, ref_egg = req.split('git+', 1)[-1].rsplit('@', 1)
            dep_links.append(url + '/tarball/' + ref_egg)

    return dep_links

DEPENDENCY_LINKS = load_github_dependency_links('requirements.txt')
DEPENDENCY_LINKS.extend(load_github_dependency_links('requirements-dev.txt'))

setup_args = dict(
    name='TDS',
    version=tds.version.__version__,
    description='Tagged Deployment System',
    # long_description = long_description,
    author='Kenneth Lareau',
    author_email='klareau@tagged.com',
    license='MIT',
    packages=list(discover_packages('tds')),
    install_requires=REQUIREMENTS['install'],
    entry_points={
        'console_scripts': [
            'tds = tds.scripts.tds_prog:main',
            'tds_install = tds.scripts.tds_install:main',
            'unvalidated_deploy_check = tds.scripts.unvalidated_deploy_check:main',
            'update_deploy_repo = tds.scripts.update_deploy_repo:daemon_main',
        ]
    },
    data_files=[
        ('share/tds/salt', ['share/salt/tds.py']),
    ],
    test_suite='tests',
    tests_require=REQUIREMENTS['install'] + REQUIREMENTS['tests'],
    dependency_links=DEPENDENCY_LINKS,
    cmdclass=dict(test=PyTest)
)

if __name__ == '__main__':
    setup(**setup_args)
