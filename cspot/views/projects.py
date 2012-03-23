from cspot.models import DBSession
from cspot.models.users import User

from cspot.models.projects import Project
from cspot.models.forms import widget_factory

from cspot.util import plural_to_singular
from cspot.util import validate_email

from cspot.auth import get_temp_user
from cspot.auth import get_user

from cspot.views.forms import FormController
from cspot.widgets import all_widget_types
from cspot.widgets.multiple_choice import MultipleChoiceWidget
from cspot.widgets.paragraph_text import ParagraphTextWidget

from pyramid.url import route_url
from pyramid.view import view_config

from pyramid.security import remember

from pyramid.httpexceptions import HTTPFound

import smtplib

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
        'link':route_url('project:team', request, project_id=project.id)
    })

    items.append({
        'num':4,
        'classes':[
            test(False, 'complete',''),
            test(section=='distribute','active','')
        ],
        'text':'Distribute',
        'sub_text':'Send items to your team',
        'link':route_url('project:distribute', request, project_id=project.id)
    })

    items.append({
        'num':5,
        'classes':[
            test(False, 'complete',''),
            test(section=='feedback','active','')
        ],
        'text':'View Feedback',
        'sub_text':'View feedback, make decisions',
        'link':route_url('project:feedback:view', request, project_id=project.id)
    })

    return items

@view_config(route_name='project', permission='review_project')
def project(project, request):
    if project.has_role(request.user, 'owner') or project.has_role(request.user, 'administrator'):
        return HTTPFound(
            location=route_url('project:records', request, project_id=project.id)
        )
    else :
        return HTTPFound(
            location=route_url('project:feedback', request, project_id=project.id)
        )

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

    session = DBSession()

    title = request.params.get('title','')
    template_id = request.params.get('template_id', '')
    item_plural = request.params.get('item_plural','').capitalize()

    templates = session.query(Project).filter(Project.template==True).all()

    if request.method == 'POST':

        if request.user and request.user.projects_remaining() <= 0:
            # Cannot add a project if you own more than 
            # your plan allows for.
            return HTTPFound(
                location=route_url('project:add', request)
            )

        if template_id != 'other':
            template = session.query(Project).filter(Project.template==True).filter(Project.id==template_id).first()
        else:
            template = None

        if not title:
            request.session.flash('Oops! Please complete all fields to continue', 'errors')

        elif template:
            # Create a new project from a template

            if not request.user:
                user = get_temp_user()
                headers = remember(request, user.id)
            else:
                user = request.user
                headers = None

            project = Project(title, 'item', 'items')
            project.add_user(user, 'owner')

            template.copy_to(project)

            for widget in template.item_form.widgets:
                widget_class = widget_factory(widget.widget_type)
                new_widget = widget_class(project.item_form, 'widget')
                widget.copy_to(new_widget)

            for widget in template.feedback_form.widgets:
                widget_class = widget_factory(widget.widget_type)
                new_widget = widget_class(project.feedback_form, 'widget')
                widget.copy_to(new_widget)

            session.add(project)
            session.flush() 

            request.session.flash('Project created', 'messages')

            return HTTPFound(
                location=route_url('project:records', request, project_id=project.id),
                headers=headers
            )

        elif item_plural:
            # Create a custom project from an item name

            item_name = plural_to_singular(item_plural)

            if not request.user:
                user = get_temp_user()
                headers = remember(request, user.id)
            else:
                user = request.user
                headers = None

            project = Project(title, item_name, item_plural)
            project.add_user(user, 'owner')

            rate_question = MultipleChoiceWidget(project.feedback_form, 'Rate this %s' % (project.item_name))
            rate_question.set_choices(['Very Good', 'Good', 'Average', 'Poor', 'Very Poor'])

            comments_question = ParagraphTextWidget(project.feedback_form, 'Comments')

            session.add(project)
            session.flush() 

            request.session.flash('Project created', 'messages')

            return HTTPFound(
                location=route_url('project:records', request, project_id=project.id),
                headers=headers
            )

    return dict(
        title=title,
        item_plural=item_plural,
        templates=templates,
    )

@view_config(route_name='project:delete', permission='manage_project')
def project_delete(project, request):
    if request.method != 'POST' or \
       request.session.get_csrf_token() != request.POST['csrf_token']:
        return HTTPFound(
            location=route_url('project:settings',request,project_id=project.id)
        )
    else:
        session = DBSession()
        session.delete(project)
        request.session.flash('%s deleted' % project.name, 'mesages')
        return HTTPFound(
            location=route_url('project:list',request)
        )
        

@view_config(route_name='project:settings', permission='manage_project',
             renderer='cspot:templates/projects/settings.pt')
def project_settings(project, request):
    if request.method == 'POST':
        name = request.params.get('name','').strip()
        item_name = request.params.get('item_name','').strip()
        item_plural = request.params.get('item_plural','').strip()
        item_label = request.params.get('item_label','').strip()

        if not (name and item_name and item_plural and item_label):
            request.session.flash('Please complete all fields!', 'errors')
        else:
            project.name = name
            project.item_name = item_name
            project.item_plural = item_plural
            project.item_label = item_label
            request.session.flash('Project settings saved!', 'messages')
        
    return dict(
        project=project,
        menu=project_menu(project, request, '')
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

@view_config(route_name='project:team', permission='manage_project',
             renderer='cspot:templates/projects/team_members.pt')
def team_members(project, request):
    """
    View team members
    """

    return dict(
        project=project,
        users=project.get_users(),
        menu=project_menu(project, request, 'team'),
    )

@view_config(route_name='project:team:add', permission='manage_project',
             renderer='cspot:templates/projects/team_members.pt')
def team_member_add(project, request):
    """
    Add team member to the project
    """

    if request.method == 'POST':
        email = request.params.get('email','')

        if not validate_email(email):
            request.session.flash('Invalid e-mail address', 'errors')
        else:
            user = get_user(email=email)

            if user is None:
                user = User(email)

            if project.get_user_roles(user):
                request.session.flash('%s is already part of this team' % email, 'errors')
            else:
                project.add_user(user, 'reviewer')
                request.session.flash('%s added' % email, 'messages')

                return HTTPFound(
                    location=route_url('project:team', request, project_id=project.id)
                )

    return dict(
        project=project,
        users=project.get_users(),
        menu=project_menu(project, request, 'team'),
    )

@view_config(route_name='project:team:remove', permission='manage_project',
             renderer='cspot:templates/projects/team_members.pt')
def team_member_remove(project, request):
    """
    Remove a team member
    """

    user_id = request.matchdict['user_id']

    user = get_user(user_id=user_id)

    if 'owner' in project.get_user_roles(user):
        request.session.flash('Cannot remove a project\'s owner', 'errors')

    elif user:
        project.remove_user(user)

        request.session.flash('%s removed' % user.email, 'messages')

        return HTTPFound(
            location=route_url('project:team', request, project_id=project.id)
        )

    return dict(
        project=project,
        users=project.get_users(),
        menu=project_menu(project, request, 'team'),
    )

@view_config(route_name='project:distribute', permission='manage_project',
             renderer='cspot:templates/projects/distribute.pt')
def distribute(project, request):
    """
    Distribute items to the team
    """

    if request.method == 'POST':
        submit = request.params.get('submit','')
        item_ids = request.params.getall('item_ids')
        message = request.params.get('message','').strip()

        if submit == 'all':
            item_ids = [i.id for i in project.items_to_distribute()]

        if not item_ids:
            request.session.flash('Oops! Please select one or more items to distribute, or choose "Distribute All"','errors')
            
        else:
            count = 0
            for item_id in item_ids:
                item = project.get_item(item_id)
                if item: 
                    item.distribute()
                    count += 1

            data = {
                'from_name':request.user.name,
                'from_address':request.user.email,
                'project_name':project.name,
                'item_plural':project.item_plural,
                'feedback_url':route_url('project:feedback',request, project_id=project.id),
                'count':count,
                'message':message
            }

            settings = request.registry.settings

            server = smtplib.SMTP(settings['cspot.email_server'])
            server.login(settings['cspot.email_user'], settings['cspot.email_password'])

            for user_role in project.user_roles:
                user = user_role.user
                data['to_address'] = user.email
                data['to_name'] = user.name

                msg = u"""
To: %(to_address)s
Reply-To: %(from_address)s
From: %(from_name)s by way of CommitteeSpot <team@committeespot.com>
Subject: %(project_name)s %(item_plural)s

%(to_name)s,

%(count)s new %(item_plural)s are ready for your review for %(project_name)s.

To provide your feedback login at:

%(feedback_url)s
                """ % data

                if not user.password_hash:
                    data['to_password'] = user.generate_password()

                    msg += u"""
Login using your e-mail address and the password below.

E-mail: %(to_address)s
Password: %(to_password)s
                    """ % data
                else:
                    msg += u"""
Login using your e-mail address and your CommitteeSpot password.
                    """

                if message:
                    msg += u"""
Message from %(from_name)s:

%(message)s
                    """ % data

                msg = msg.strip()

                server.sendmail('team@committeespot.com', user.email, msg)

            server.quit()
            request.session.flash('%s items distributed' % len(item_ids), 'messages')

    items_to_distribute = project.items_to_distribute()

    if project.is_owner_temporary():
        show_section = 'temporary_account'
    elif not project.items or not project.feedback_form.has_widgets():
        show_section = 'incomplete'
    elif not items_to_distribute:
        show_section = 'no_items'
    else:
        show_section = 'items'

    return dict(
        project=project,
        items_to_distribute=items_to_distribute,
        show_section=show_section,
        menu=project_menu(project, request, 'distribute')
    )

@view_config(route_name='project:distribute:history', permission='manage_project',
             renderer='cspot:templates/projects/distribute_history.pt')
def distribute_history(project, request):
    """
    Show distribution history
    """

    return dict(
        project=project,
        menu=project_menu(project, request, 'distribute')
    )
