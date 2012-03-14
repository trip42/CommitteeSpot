from cspot.models import DBSession
from cspot.models.forms import Form
from cspot.models.projects import Project

from cspot.models.forms import Widget
from cspot.models.forms import MultipleChoiceWidget
from cspot.models.forms import FileUploadWidget

from cspot.util import plural_to_singular
from cspot.auth import get_temp_user

from pyramid.url import route_url
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.security import remember

from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound


def widget_controller_factory(widget):
    """
    Generates a widget controller from a
    widget object
    """

    for model, controller in widget_type_map:
        if model.widget_type == widget.widget_type:
            return controller(widget)

    raise StandardError("Invalid Widget Type")

def widget_factory(widget_type):
    """
    Generate a widget model class for a type
    """

    for model, controller in widget_type_map:
        if model.widget_type == widget_type:
            return model

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

    def get_value(self, request):
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
       
class MultipleChoiceWidgetController(IWidgetController):
    def data(self):
        return dict(
            choices=self.widget.get_choices()
        )

    def options(self, request):
        return render(
            'cspot:templates/widgets/multiple_choice_options.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
            ),
            request
        )

    def process_options(self, request):
        choices = request.params.getall('choices')
        label = request.params.get('label',None)

        self.widget.set_choices(choices)
        self.widget.label = label

        session = DBSession()
        session.add(self.widget)

    def render(self, value, request):
        return render(
            'cspot:templates/widgets/multiple_choice.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
            ),
            request
        )

class FileUploadWidgetController(IWidgetController):
    def options(self, request):    
        return render(
            'cspot:templates/widgets/file_upload_options.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
            ),
            request
        )

    def process_options(self, request):
        label = request.params.get('label',None)
        self.widget.label = label

        session = DBSession()
        session.add(self.widget)

    def render(self, value, request):
        return render(
            'cspot:templates/widgets/file_upload.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
            ),
            request
        )

widget_type_map = [
    (MultipleChoiceWidget, MultipleChoiceWidgetController),
    (FileUploadWidget, FileUploadWidgetController),
]

class FormController(object):
    """
    Common form processing
    """
 
    def __init__(self, form):
        self.form = form
        self.widget_controllers = dict([(widget.id, widget_controller_factory(widget)) for widget in self.form.widgets])

    def render_widgets(self, request, record=None):
        """
        return a list of rendered HTML for each form element in the form.
        XXX should accept a record to populate the values from
        """

        widget_controllers = [widget_controller_factory(w) for w in self.form.widgets]
        return [w.render(None, request) for w in widget_controllers]

class WidgetView(object):
    """
    Collection of views associated with form processing.
    """

    def __init__(self, project, request):
        session = DBSession()

        self.project = project
        self.request = request

        self.form_id = request.matchdict.get('form_id', None)
        self.form = session.query(Form).filter(Form.project==self.project).filter(Form.id==self.form_id).first()

        self.widget_id = request.matchdict.get('widget_id', None)
        self.widget = session.query(Widget).filter(Widget.form==self.form).filter(Widget.id==self.widget_id).first()

    @view_config(route_name='form:widget', 
                 permission='manage_project',
                 renderer='string')
    def widget(self):
        """
        Renders a single widget to HTML
        """

        widget_controller = widget_controller_factory(self.widget)
        return widget_controller.render(self.request)
    
    @view_config(route_name='form:widget:options', 
                 permission='manage_project',
                 renderer='json')
    def widget_options(self):
        """
        Renders the options panel for a single widget
        """

        widget_controller = widget_controller_factory(self.widget)

        if self.request.method == 'POST':
            widget_controller.process_options(self.request)

        return dict(
            id=self.widget.id,
            type=self.widget.widget_type,
            options_html=widget_controller.options(self.request),
            widget_html=widget_controller.render(None, self.request),
            data=widget_controller.data(),
        )

    @view_config(route_name='form:widget:add', 
                 permission='manage_project',
                 renderer='json')
    def widget_add(self):
        """
        Adds a widget given a widget_type to the current
        form
        """

        session = DBSession()

        widget_type = self.request.params.get('widget_type', None)
        widget_model = widget_factory(widget_type)
        
        widget = widget_model(self.form, 'Untitled')
        session.add(widget)
        session.flush()

        widget_controller = widget_controller_factory(widget)

        return dict(
            id=widget.id,
            type=widget_type,
            widget_html=widget_controller.render(None, self.request),
            data=widget_controller.data(),
        )

    @view_config(route_name='form:widget:delete', 
                 permission='manage_project',
                 renderer='json')
    def widget_delete(self):
        """
        Delete a widget from the current form
        """

        session = DBSession()
        widget_controller = widget_controller_factory(self.widget)
        widget_controller.delete()

        return dict(
            id=self.widget.id,
        )



