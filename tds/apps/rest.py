import tds.views.rest

from tds.apps import TDSProgramBase


# Initialize connection to database (for session handling)
rest_api = TDSProgramBase({'user_level': 'admin'})
rest_api.initialize_db()

application = tds.views.rest.config.make_wsgi_app()
