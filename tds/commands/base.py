import tds.authorize


class BaseController(object):
    access_levels = {}

    def __init__(self, config):
        self.app_config = config

    def action(self, action, **params):
        required_access_level = self.access_levels.get(action, 'disabled')

        if required_access_level is not None:
            if required_access_level == 'environment':
                required_access_level = params.get('environment')

            # TODO: make this return an auth exception
            tds.authorize.verify_access(
                params.get('user_level', 'disabled'),
                required_access_level
            )

        handler = getattr(self, action, None)
        if handler is None:
            return dict(error=Exception(
                "Unknown action for %s: %s", type(self).__name__, action
            ))

        try:
            return handler(**params)
        except Exception as exc:
            return dict(error=exc)
