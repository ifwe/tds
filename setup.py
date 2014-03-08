from setuptools import setup
import sys

# Let's add this later
# long_description = open('README.txt').read()

# Get version of project
import tds.version

with open('requirements.txt', 'r') as reqfile:
    reqs = reqfile.read()

REQUIREMENTS = []

PYTHON27_REQ_BLACKLIST = ['argparse', 'ordereddict']

for req in filter(None, reqs.strip().splitlines()):
    if req.startswith('git+'):
        req = '=='.join(req.rsplit('=')[-1].rsplit('-', 1))
    if sys.version_info > (2,7) or sys.version_info > (3, 2):
        if any(req.startswith(bl) for bl in PYTHON27_REQ_BLACKLIST):
            continue
    REQUIREMENTS.append(req)

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
              'tds.utils'
              ],
    install_requires = REQUIREMENTS,
    entry_points = {
        'console_scripts': [
            'tds = tds.scripts.tds_prog:main',
            'unvalidated_deploy_check = tds.scripts.unvalidated_deploy_check:main',
            'update_deploy_repo = tds.scripts.update_deploy_repo:daemon_main',
        ]
    },
)

if __name__ == '__main__':
    setup(**setup_args)
