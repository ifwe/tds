from setuptools import setup

# Let's add this later
# long_description = open('README.txt').read()

# Get version of project
import tds.version

setup_args = dict(
    name='TDS',
    version=tds.version.__version__,
    description='Tagged Deployment System',
    # long_description = long_description,
    author='Kenneth Lareau',
    author_email='klareau@tagged.com',
    license='Apache License, Version 2.0',
    packages=[
              'tds',
              'tds.deploy_strategy',
              'tds.notifications',
              'tds.scripts',
              'tds.utils'
              ],
    entry_points = {
        'console_scripts': [
            'tds = tds.scripts.tds:main',
            'unvalidated_deploy_check = tds.scripts.unvalidated_deploy_check:main',
            'update_deploy_repo = tds.scripts.update_deploy_repo:daemon_main',
        ]
    },
)

if __name__ == '__main__':
    setup(**setup_args)
