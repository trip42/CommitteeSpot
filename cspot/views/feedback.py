from cspot.models import DBSession
from cspot.models.records import ItemRecord
from cspot.models.records import FeedbackRecord

from pyramid.url import route_url
from pyramid.view import view_config

from cspot.views.projects import project_menu
from cspot.views.forms import FormController

from pyramid.httpexceptions import HTTPFound

@view_config(route_name='project:feedback', permission='review_project',
             renderer='cspot:templates/projects/feedback.pt')
@view_config(route_name='project:feedback:item', permission='review_project',
             renderer='cspot:templates/projects/feedback.pt')
def feedback(project, request):
    session = DBSession()

    item_id = request.matchdict.get('item_id',None)
    items = project.get_items_for_user(request.user)
    pending_items = [i for i in items if not i.submitted]
    completed_items = [i for i in items if i.submitted]

    if item_id:
        item = project.get_item_for_user(request.user, item_id)
    elif pending_items:
        item = pending_items[0]
    else:
        item = None

    if item is not None:
        item = project.get_item(item.id)
        feedback = session.query(FeedbackRecord).filter(FeedbackRecord.user==request.user).filter(FeedbackRecord.item==item).first()
    else:
        feedback = None

    item_controller = FormController(project.item_form)
    feedback_controller = FormController(project.feedback_form)

    if request.method == 'POST' and item:
        if not feedback:
            feedback = FeedbackRecord(project, request.user, item)
            session.add(feedback)

        feedback.update_submitted()
        feedback_controller.populate_record_from_request(feedback, request)

        request.session.flash('Feedback on %s submitted' % item.title, 'messages')

        # Once feedback is submitted, load the next
        # record from the top of the list

        if request.params.get('submit','') == 'save_and_next':
            return HTTPFound(
                location=route_url('project:feedback', request, project_id=project.id)
            )
        else:
            return HTTPFound(
                location=route_url('project:feedback:item', request, project_id=project.id, item_id=item.id)
            )

    return dict(
        pending_items=pending_items,
        completed_items=completed_items,
        item=item,
        item_values=item_controller.render_values(request, item),
        form_widgets=feedback_controller.render_widgets(request, feedback),
        project=project,
        responsive_layout=True,
    )

@view_config(route_name='project:feedback:view', permission='manage_project',
             renderer='cspot:templates/projects/feedback_view.pt')
def feedback_view(project, request):
    items = project.items_distributed()

    feedback_controller = FormController(project.feedback_form)

    item_summaries = []

    for item in items:
        item_summaries.append(dict(
            item=item,
            summary=feedback_controller.render_feedback_summary(request, item.feedback)
        ))

    return dict(
        project=project,
        item_summaries=item_summaries,
        menu=project_menu(project, request, 'feedback')
    )

