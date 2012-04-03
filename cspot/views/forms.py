from pyramid.url import route_url
from pyramid.view import view_config

from cspot.models.projects import Project

from cspot.models import DBSession

from cspot.models.forms import widget_factory
from cspot.models.forms import Form
from cspot.models.forms import Widget

from cspot.models.records import Record
from cspot.models.records import Value

from cspot.widgets import all_widget_types

def widget_controller_factory(widget):
    """
    Generates a widget controller from a
    widget object
    """

    for model, controller in all_widget_types:
        if model.widget_type == widget.widget_type:
            return controller(widget)

    raise StandardError("Invalid Widget Type")

class FormController(object):
    """
    Common form processing
    """
 
    def __init__(self, form):
        self.form = form
        self.widget_controllers = dict([(widget.id, widget_controller_factory(widget)) for widget in self.form.widgets])

    def get_widget_controller(self, widget_id):
        return self.widget_controllers.get(int(widget_id), None)

    def render_widgets(self, request, record=None):
        """
        return a list of rendered HTML for each form element in the form.
        """

        widgets = []

        for widget in self.form.widgets:
            widget_controller = widget_controller_factory(widget)
            
            if record is not None:
                value = record.get_widget_value(widget)
            else:
                value = None

            widget_html = widget_controller.render(value, request)
            widgets.append(widget_html)

        return widgets

    def render_values(self, request, record=None):
        """
        return a list of read-only rendered HTML for each form element in the form.
        """

        widgets = []

        for widget in self.form.widgets:
            widget_controller = widget_controller_factory(widget)
            
            if record is not None:
                value = record.get_widget_value(widget)
            else:
                value = None

            widget_html = widget_controller.render_value(value, request)
            widgets.append(widget_html)

        return widgets

    def populate_record_from_request(self, record, request):
        """
        Given a record and a request create or update
        values on the record for each widget in the form
        """

        widget_controllers = [widget_controller_factory(w) for w in self.form.widgets]

        for widget_controller in widget_controllers:
            widget_controller.populate_record_from_request(record, request)
      
    def download_widget(self, request, record, widget_id):
        widget_controller = self.get_widget_controller(widget_id)
        value = record.get_widget_value(widget_controller.widget)
        return widget_controller.download(value, request)
         
class IWidgetController(object):
    """
    Interface for widget controllers.
    """

    def __init__(self, widget):
        self.widget = widget

    def field_id(self):
        return 'widget-%s' % self.widget.id

    def data(self):
        """
        Return extra data necessary for the 
        options view. Data is sent JSON encoded
        to form view.
        """

        return {}

    def options(self, request):
        """
        Render the widget options panel
        """
        raise NotImplementedError
 
    def process_options(self, request):
        """
        Process the options for the widget
        from the request
        """
        raise NotImplementedError

    def render(self, value, request):
        """
        Render a widget with the given value
        """
        raise NotImplementedError

    def render_value(self, value, request):
        """
        Render a read-only widget given a value
        """
        raise NotImplementedError

    def render_feedback_for_items(self, items, request):
        """
        Summarize the responses to this widget for all items
        """
        raise NotImplementedError

    def render_feedback_for_item(self, item, request):
        """
        Summarize the responses to this widget for a single item
        """

    def value(self, value):
        """
        return the value as a string
        """
        raise NotImplementedError

    def download(self, value, filename, request):
        """
        return a Response object which represents a
        download of this file
        """
        raise NotImplementedError

    def populate_record_from_request(self, record, request):
        """
        Generate a value from the request
        """
        raise NotImplementedError

    def delete(self):
        """
        Delete the widget
        """

        session = DBSession()
        session.delete(self.widget)

@view_config(route_name='form:widget:options', 
             permission='manage_project',
             http_cache=0,
             renderer='json')
def widget_options(project, request):
    """
    Renders the options panel for a single widget
    """

    session = DBSession()

    form_id = request.matchdict.get('form_id', None)
    form = session.query(Form).filter(Form.project_id==project.id).filter(Form.id==form_id).first()

    widget_id = request.matchdict.get('widget_id', None)
    widget = session.query(Widget).filter(Widget.form==form).filter(Widget.id==widget_id).first()

    widget_controller = widget_controller_factory(widget)

    if request.method == 'POST':
        widget_controller.process_options(request)

    return dict(
        id=widget.id,
        type=widget.widget_type,
        options_html=widget_controller.options(request),
        widget_html=widget_controller.render(None, request),
        data=widget_controller.data(),
    )

@view_config(route_name='form:widget:add', 
             permission='manage_project',
             http_cache=0,
             renderer='json')
def widget_add(project, request):
    """
    Adds a widget given a widget_type to the current
    form
    """

    session = DBSession()

    form_id = request.matchdict.get('form_id', None)
    form = session.query(Form).filter(Form.project_id==project.id).filter(Form.id==form_id).first()

    widget_type = request.params.get('widget_type', None)
    widget_model = widget_factory(widget_type)
    
    widget = widget_model(form, 'Untitled')
    session.add(widget)
    session.flush()

    widget_controller = widget_controller_factory(widget)

    return dict(
        id=widget.id,
        type=widget_type,
        widget_html=widget_controller.render(None, request),
        data=widget_controller.data(),
    )

@view_config(route_name='form:widget:delete', 
             permission='manage_project',
             http_cache=0,
             renderer='json')
def widget_delete(project, request):
    """
    Delete a widget from the current form
    """

    session = DBSession()

    form_id = request.matchdict.get('form_id', None)
    form = session.query(Form).filter(Form.project_id==project.id).filter(Form.id==form_id).first()

    widget_id = request.matchdict.get('widget_id', None)
    widget = session.query(Widget).filter(Widget.form==form).filter(Widget.id==widget_id).first()

    session = DBSession()
    widget_controller = widget_controller_factory(widget)
    widget_controller.delete()

    return dict(
        id=widget.id,
    )

@view_config(route_name='form:widget:sort_order', 
             permission='manage_project',
             http_cache=0,
             renderer='json')
def widget_sort_order(project, request):
    """
    Reorder widgets by passing a list of widget
    ids named sort_order in the request
    """

    session = DBSession()

    form_id = request.matchdict.get('form_id', None)
    form = session.query(Form).filter(Form.project_id==project.id).filter(Form.id==form_id).first()

    if request.method == 'POST':
        session = DBSession()

        sort_order = request.params.getall('sort_order[]')

        positions = {}
        for idx, widget_id in enumerate(sort_order):
            positions[int(widget_id)] = idx

        for widget in form.widgets:
            # get the sort order for this widget
            # if it's not included in the submitted values
            # return the next position and add it back into
            # the submitted values
            sort_order = positions.get(widget.id, len(positions))
            positions[widget.id] = sort_order
       
            widget.sort_order = sort_order 
            session.add(widget)

    return {}
