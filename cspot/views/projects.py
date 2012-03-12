from cspot.models import DBSession
from cspot.models.users import User
from cspot.models.projects import Project

from cspot.util import plural_to_singular
from cspot.auth import get_temp_user

from pyramid.url import route_url
from pyramid.view import view_config

from pyramid.security import remember

from pyramid.httpexceptions import HTTPFound

def project_factory(request):
    """
    Generate a project from the project_id in the url
    """

    session = DBSession()
    project_id = request.matchdict.get('project_id', None)

    if project_id:
        return session.query(Project).filter(Project.id==project_id).first()
    else:
        return None

@view_config(route_name='project:list', 
             permission='view_restricted',
             renderer='cspot:templates/projects/list.pt')
def project_list(request):
    """
    Show a list of projects for the authenticated
    user.
    """

    return dict(
        project_roles=request.user.project_roles
    )

@view_config(route_name='project:add',
             renderer='cspot:templates/projects/add.pt')
def projects_add(request):
    """
    Add a project owned by the current user
   
    if a user is not logged in create a temporary user
    and associate the project with that user
    """

    title = request.params.get('title','')
    item_plural = request.params.get('item_plural','').capitalize()

    if request.method == 'POST':
        if not (title and item_plural):
            request.session.flash('Oops! Please complete all fields to continue', 'errors')

        else:
            item_name = plural_to_singular(item_plural)

            if not request.user:
                user = get_temp_user()
                headers = remember(request, user.id)
            else:
                headers = None

            project = Project(title, item_name, item_plural)
            project.add_user(user, 'owner')

            session = DBSession()
            session.add(project)
            session.flush() 

            request.session.flash('Project created', 'messages')

            return HTTPFound(
                location=route_url('project:records', request, project_id=project.id),
                headers=headers
            )

    return dict(
        title=title,
        item_plural=item_plural
    )

