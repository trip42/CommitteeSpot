from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from cspot.models import initialize_sql

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    # Initialize database
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)

    config = Configurator(settings=settings)
    config.scan()

    config.add_route('home', '/')

    return config.make_wsgi_app()

