fake_config = {
    'deploy': {
        'env': {'environment': 'fakedev'},
        'logging': {
            'syslog_facility': 'fakelocal3',
            'syslog_priority': 'fakedebug'
        },
        'notifications': {
            'enabled_methods': ['email', 'hipchat'],
            'validation_time': -1,
            'email': {'receiver': 'fake@example.com'},
            'hipchat': {
                'rooms': ['fakeroom'],
                'token': 'deadbeef',
            },
        },
        'repo': {
            'build_base': '/fake/mnt/deploy/builds',
            'incoming': '/fake/mnt/deploy/incoming',
            'processing': '/fake/mnt/deploy/processing'
        }
    },
    'database': {
        'db': {
            'user': 'fakityfake',
            'password': 'superpassword'
        }
    }
}
