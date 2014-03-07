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
    packages=['tds', 'tds.utils'],
    scripts=['bin/tds',
             'bin/unvalidated_deploy_check',
             'bin/update_deploy_repo', ],
)

if __name__ == '__main__':
    setup(**setup_args)
