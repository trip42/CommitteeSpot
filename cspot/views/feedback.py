from cspot.models import DBSession
from cspot.models.records import ItemRecord
from cspot.models.records import FeedbackRecord

from pyramid.url import route_url
from pyramid.view import view_config
from pyramid.response import Response

from cspot.views.projects import project_menu
from cspot.views.forms import FormController
from cspot.views.forms import widget_controller_factory

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

@view_config(route_name='project:feedback:by_item', permission='manage_project',
             renderer='cspot:templates/projects/feedback_by_item.pt')
def feedback_view_by_item(project, request):
    items = project.items_distributed()

    feedback_controller = FormController(project.feedback_form)

    summaries = []

    for item in items:
        widget_summaries = []
        for widget in project.feedback_form.widgets:
            widget_controller = widget_controller_factory(widget)
            widget_summaries.append({
                'title':widget.label,
                'summary':widget_controller.render_feedback_for_item(item, request)
            })

        summaries.append({
            'title':item.title,
            'widgets':widget_summaries
        })

    return dict(
        project=project,
        summaries=summaries,
        menu=project_menu(project, request, 'feedback')
    )

@view_config(route_name='project:feedback:view', permission='manage_project',
             renderer='cspot:templates/projects/feedback_by_widget.pt')
def feedback_view_by_widget(project, request):
    items = project.items_distributed()

    summaries = []

    for widget in project.feedback_form.widgets:
        widget_controller = widget_controller_factory(widget)
        summaries.append(dict(
            title=widget.label,
            summary=widget_controller.render_feedback_for_items(items, request)
        ))

    return dict(
        project=project,
        summaries=summaries,
        menu=project_menu(project, request, 'feedback')
    )

@view_config(route_name='project:feedback:download', permission='manage_project')
def feedback_download(project, request):
    items = project.items_distributed()

    feedback_controller = FormController(project.feedback_form)

    import csv
    import StringIO

    file = StringIO.StringIO()
    writer = csv.writer(file)

    headers = ['Reviewer', project.item_label]
    widget_controllers = []

    for widget in project.feedback_form.widgets:
        widget_controllers.append(widget_controller_factory(widget))
        headers.append(widget.label)

    writer.writerow(headers)

    for item in items:
        for feedback in item.feedback:
            row = [feedback.user.name, item.title]

            for widget_controller in widget_controllers:
                value = feedback.get_widget_value(widget_controller.widget)
                row.append(widget_controller.value(value))

            writer.writerow(row)

    csv_data = file.getvalue()
    file.close()

    return Response(csv_data, content_type='text/csv', content_disposition='attachment; filename=feedback.csv')

