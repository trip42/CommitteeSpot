from cspot.models import DBSession
from pyramid.view import view_config

@view_config(route_name='home', renderer='cspot:templates/home.pt')
@view_config(route_name='terms', renderer='cspot:templates/terms.pt')
@view_config(route_name='privacy', renderer='cspot:templates/privacy.pt')
def static_page(request):
    session = DBSession()
    return {}

