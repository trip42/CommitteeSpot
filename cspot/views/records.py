from cspot.models import DBSession
from cspot.models.users import User
from cspot.models.projects import Project

from cspot.util import plural_to_singular
from cspot.auth import get_temp_user

from cspot.views.projects import project_menu
from cspot.views.forms import FormController

from pyramid.url import route_url
from pyramid.view import view_config

from pyramid.security import remember

from pyramid.httpexceptions import HTTPFound

@view_config(route_name='project:records',
             permission='manage_project')
def record_first(project, request):
    if False and project.items.records:
        return HTTPFound(
            location=route_url('project:record', request, project_id=project.id, record_id=project.records[0].id)
        )
    else:
        return HTTPFound(
            location=route_url('project:record:add', request, project_id=project.id)
        )


@view_config(route_name='project:record:add',
             permission='manage_project',
             renderer='cspot:templates/projects/record.pt')
def record_add(project, request):
    form_controller = FormController(project.item_form)

    return dict(
        project=project,
        menu=project_menu(project, request, 'records'),
        form_widgets=form_controller.render_widgets(request),
        record=None
    )


@view_config(route_name='project:record',
             permission='manage_project',
             renderer='cspot:templates/projects/record.pt')
def record(project, request):
    form_controller = FormController(project.item_form)

    return dict(
        project=project,
        menu=project_menu(project, request, 'records'),
        form_widgets=form_controller.render_widgets(request),
        record=None
    )
    

