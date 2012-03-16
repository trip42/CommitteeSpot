from cspot.models import DBSession
from cspot.models.users import User
from cspot.models.projects import Project

from cspot.util import plural_to_singular
from cspot.auth import get_temp_user

from cspot.views.forms import FormController
from cspot.widgets import all_widget_types

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

def project_menu(project, request, section='records'):
    items = []

    def test(c, t, f):
        if c: return t
        return f

    items.append({
        'num':1,
        'classes':[
            test(False, 'complete',''),
            test(section=='records','active','')
        ],
        'text':'Add %s' % project.item_plural_short(),
        'sub_text':'Add and edit items',
        'link':route_url('project:records', request, project_id=project.id)
    })

    items.append({
        'num':2,
        'classes':[
            test(False, 'complete',''),
            test(section=='feedback_form','active','')
        ],
        'text':'Ask Questions',
        'sub_text':'Questions for your team',
        'link':route_url('project:feedback_form', request, project_id=project.id)
    })

    items.append({
        'num':3,
        'classes':[
            test(False, 'complete',''),
            test(section=='team','active','')
        ],
        'text':'Your Team',
        'sub_text':'Add and edit team members',
        'link':''
    })

    items.append({
        'num':4,
        'classes':[
            test(False, 'complete',''),
            test(section=='distribute','active','')
        ],
        'text':'Distribute',
        'sub_text':'Send items to your team',
        'link':''
    })

    items.append({
        'num':5,
        'classes':[
            test(False, 'complete',''),
            test(section=='feedback','active','')
        ],
        'text':'View Feedback',
        'sub_text':'View feedback, make decisions',
        'link':''
    })

    return items

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
                user = request.user
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

@view_config(route_name='project:item_form', permission='manage_project',
             renderer='cspot:templates/projects/item_form.pt')
def item_form_view(project, request):
    """
    View for the item form
    """

    form_controller = FormController(project.item_form)

    return dict(
        project=project,
        form=project.item_form,
        menu=project_menu(project, request, 'records'),
        form_widgets=form_controller.render_widgets(request),
        widget_types=[w[0] for w in all_widget_types],
    )

@view_config(route_name='project:feedback_form', permission='manage_project',
             renderer='cspot:templates/projects/feedback_form.pt')
def feedback_form_view(project, request):
    """
    View for the feedback form
    """

    form_controller = FormController(project.feedback_form)

    return dict(
        project=project,
        form=project.feedback_form,
        menu=project_menu(project, request, 'feedback_form'),
        form_widgets=form_controller.render_widgets(request),
        widget_types=[w[0] for w in all_widget_types],
    )


