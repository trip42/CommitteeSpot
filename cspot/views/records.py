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

@view_config(route_name='project:records',
             permission='manage_project')
def record_first(project, request):
    if project.items:
        return HTTPFound(
            location=route_url('project:record', request, project_id=project.id, record_id=project.items[0].id)
        )
    else:
        return HTTPFound(
            location=route_url('project:record:add', request, project_id=project.id)
        )

@view_config(route_name='project:record:add',
             permission='manage_project',
             renderer='cspot:templates/projects/record.pt')
@view_config(route_name='project:record',
             permission='manage_project',
             renderer='cspot:templates/projects/record.pt')
def record(project, request):
    form_controller = FormController(project.item_form)

    record_id = request.matchdict.get('record_id', None)

    if record_id is not None:
        record = project.get_item(record_id)
    else:
        record = None

    if record and not record.reviewed:
        record.reviewed = True

    if request.method == 'POST':
        title = request.params.get('title', '').strip()
        submit = request.params.get('submit','')

        if not title and submit.find('finish') >= 0:
            return HTTPFound(
                location=route_url('project:feedback_form', request, project_id=project.id)
            )

        elif not title:
            request.session.flash('%s Name or Title is required!' % project.item_name, 'errors')

        elif title:
            form_controller = FormController(project.item_form)
            form_controller.validate_from_request(request)

            if form_controller.errors:
                request.session.flash('There was a problem with your submission', 'errors')

            else:
                request.session.flash('%s saved!' % title, 'messages')

                if record is None:
                    record = ItemRecord(project, title)

                record.title = title

                form_controller.populate_record_from_request(record, request)
    
                session = DBSession()
                session.add(record)
                session.flush()
    
                if submit.find('add') >= 0:
                    route = 'project:record:add'
                elif submit.find('finish') >= 0:
                    route = 'project:feedback_form'
                else:
                    route = 'project:record'
    
                return HTTPFound(
                    location=route_url(route, request, project_id=project.id, record_id=record.id)
                )

    return dict(
        project=project,
        menu=project_menu(project, request, 'records'),
        form_widgets=form_controller.render_widgets(request, record),
        record=record
    )
    

@view_config(route_name='project:record:download',
             permission='review_project')
def file_download(project, request):
    """
    Download a file from a widget
    """

    session = DBSession()

    record_id = request.matchdict['record_id']
    widget_id = request.matchdict['widget_id']
    filename = request.matchdict['filename']

    record = session.query(Record).filter(Record.project_id==project.id).filter(Record.id==record_id).first()
    widget = session.query(Widget).filter(Widget.id==widget_id).first()
    widget_controller = widget_controller_factory(widget)

    value = record.get_widget_value(widget)

    return widget_controller.download(value, filename, request)


@view_config(route_name='project:record:import', permission='review_project',
             renderer='cspot:templates/projects/premium_import.pt')
def record_import(project, request):
    return dict(
        project=project,
        menu=project_menu(project, request, 'records'),
    )

