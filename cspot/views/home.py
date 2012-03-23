from cspot.models import DBSession
from pyramid.view import view_config
from pyramid.url import route_url

@view_config(route_name='home', renderer='cspot:templates/home.pt')
@view_config(route_name='terms', renderer='cspot:templates/terms.pt')
@view_config(route_name='privacy', renderer='cspot:templates/privacy.pt')
def static_page(request):
    session = DBSession()
    return {}

from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember

@view_config(route_name='demo')
def demo(request):
    demo_key = request.matchdict['demo_key']
    settings = request.registry.settings

    if demo_key == settings['cspot.demo_admin_key']:
        headers = remember(request, settings['cspot.demo_user_id'])
        location = route_url('project:records',request,project_id=settings['cspot.demo_project_id'])
    elif demo_key == settings['cspot.demo_review_key']:
        headers = remember(request, settings['cspot.demo_user_id'])
        location = route_url('project:feedback',request,project_id=settings['cspot.demo_project_id'])
    else:
        headers = None
        location = route_url('home',request)
       
    return HTTPFound(
        location=location,
        headers=headers
    ) 
    

