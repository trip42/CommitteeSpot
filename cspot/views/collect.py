from cspot.models import DBSession
from cspot.models.users import User
from cspot.models.projects import Project
from cspot.models.forms import Widget
from cspot.models.records import Record
from cspot.models.records import ItemRecord

from cspot.util import plural_to_singular
from cspot.auth import get_temp_user

from cspot.views.projects import project_menu
from cspot.views.forms import FormController
from cspot.views.forms import widget_controller_factory

from pyramid.url import route_url
from pyramid.view import view_config
from pyramid.security import remember
from pyramid.httpexceptions import HTTPFound

@view_config(route_name='project:collect',
             renderer='cspot:templates/projects/collect.pt')
def record_collect(request):
    session = DBSession()

    collect_code = request.matchdict['collect_code']

    project = session.query(Project).filter(Project.collect_code == collect_code).first()

    form_controller = FormController(project.item_form)

    if request.method == 'POST':
        title = request.params.get('title', '').strip()
        submit = request.params.get('submit','')

        if not title and submit.find('finish') >= 0:
            return HTTPFound(
                location=route_url('project:collect', request, project_id=project.id)
            )

        elif not title:
            request.session.flash('%s Name or Title is required!' % project.item_name, 'errors')

        elif title:
            form_controller = FormController(project.item_form)
            form_controller.validate_from_request(request)

            if form_controller.errors:
                request.session.flash('There was a problem with your submission', 'errors')

            else:
                record = ItemRecord(project, title)
                record.title = title
                record.reviewed = False

                form_controller.populate_record_from_request(record, request)
    
                session.add(record)
                session.flush()
    
                return HTTPFound(
                    location=route_url('project:collect:thanks', request, collect_code=project.collect_code)
                )

    return dict(
        project=project,
        form_widgets=form_controller.render_widgets(request, None)
    )
    

@view_config(route_name='project:collect:settings', permission='manage_project',
             renderer='cspot:templates/projects/collect_settings.pt')
def record_collect_settings(project, request):
    return dict(
        project=project,
        menu=project_menu(project, request, 'records'),
    )

@view_config(route_name='project:collect:thanks',
             renderer='cspot:templates/projects/collect_thanks.pt')
def record_collect_thanks(request):
    session = DBSession()
    collect_code = request.matchdict['collect_code']
    project = session.query(Project).filter(Project.collect_code == collect_code).first()

    return dict(
        project=project
    )


