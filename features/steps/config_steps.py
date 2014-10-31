"""Environment configuration for feature tests"""

import yaml
from behave import given

import tds.commands
import tagopsdb


@given(u'I am in the "{env}" environment')
def given_i_am_in_environment(context, env):
    with open(context.TDS_CONFIG_FILE) as f:
        config = yaml.load(f.read())

    config['env']['environment'] = env

    with open(context.TDS_CONFIG_FILE, 'wb') as f:
        f.write(yaml.dump(config))

    context.tds_env = env
    environment = tds.commands.DeployController.envs.get(env, env)
    context.tds_environment = environment.decode('utf8')

    if 'no_db' not in context.tags:
        domain = env + 'example.com'
        tagopsdb.Session.add(tagopsdb.Zone(zone_name=domain))
        tagopsdb.Session.flush()
        tagopsdb.Session.add(tagopsdb.Environment(
            env=env,
            environment=tds.commands.DeployController.envs.get(env, env),
            domain=domain,
            prefix=env[0],
            zone_id=tagopsdb.Zone.get(zone_name=domain).id
        ))
        tagopsdb.Session.commit()
