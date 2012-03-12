from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.session import UnencryptedCookieSessionFactoryConfig

from cspot.models import initialize_sql
from cspot.auth import role_finder
from cspot.auth import root_factory

from cspot.middleware import RequestWithUser

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    # Initialize database
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)

    authentication_policy = AuthTktAuthenticationPolicy(
        secret='lkjasy222nna!235happy',
        callback=role_finder,
        include_ip=True,
        reissue_time=720,
        http_only=True
    )

    authorization_policy = ACLAuthorizationPolicy()

    session_factory = UnencryptedCookieSessionFactoryConfig('1babble235tomorrow+')

    config = Configurator(
        settings=settings,
        root_factory=root_factory,
        authentication_policy=authentication_policy,
        authorization_policy=authorization_policy,
        session_factory=session_factory
    )

    config.scan()

    config.set_request_factory(RequestWithUser) 

    config.include('cspot.routes')

    config.add_view('cspot.views.auth.forbidden',
                    context='pyramid.httpexceptions.HTTPForbidden',
                    renderer='templates/forbidden.pt')

    return config.make_wsgi_app()

