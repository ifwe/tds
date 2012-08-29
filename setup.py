from setuptools import setup, find_packages

# Let's add this later
# long_description = open('README.txt').read()

setup_args = dict(
    name = 'TDS',
    version = '0.5.0',
    description = 'Tagged Deployment System',
    # long_description = long_description,
    author = 'Kenneth Lareau',
    author_email = 'klareau@tagged.com',
    license = 'MIT',
    packages = ['tds'],
    package_dir = {'' : 'lib/python'},
    scripts = ['bin/tds',
               'bin/manage_deploy_rpms',
               'bin/update_deploy_repo',],
)

if __name__ == '__main__':
    setup(**setup_args)
