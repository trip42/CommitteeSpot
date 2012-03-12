from cspot.models import DBSession
from pyramid.view import view_config

@view_config(route_name='home', renderer='cspot:templates/home.pt')
def home(request):
    session = DBSession()
    return {}
