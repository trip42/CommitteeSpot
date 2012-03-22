from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText

from cspot.models import DBSession
from cspot.models.forms import Widget
from cspot.models.records import Value

from cspot.views.forms import IWidgetController
from cspot.widgets import register_widget

from pyramid.renderers import render

import simplejson

class ParagraphTextWidget(Widget):
    widget_type = 'paragraph_text'
    name = 'Paragraph Text'

    __mapper_args__ = {'polymorphic_identity':widget_type}

    def __init__(self, form, label):
        Widget.__init__(self, form, label)

class ParagraphTextValue(Value):
    __mapper_args__ = {'polymorphic_identity':'paragraph_text'}

    def set_value(self, value):
        self.text_value = value

    def get_value(self):
        return self.text_value

class ParagraphTextController(IWidgetController):
    def options(self, request):
        return render(
            'options.pt',
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
            'render.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
                value=value,
            ),
            request
        )

    def render_value(self, value, request):
        if value:
            value = value.get_value()
        else:
            value = 'n/a'

        return render(
            'value.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
                value=value,
            ),
            request
        )

    def render_feedback_summary(self, values, request):
        return render(
            'summary.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
                values=values
            ),
            request
        )

    def value(self, value):
        return value.get_value()

    def populate_record_from_request(self, record, request):
        session = DBSession()
        value = session.query(ParagraphTextValue).filter(Value.record==record).filter(Value.widget==self.widget).first()

        if not value:
            value = ParagraphTextValue(record, self.widget)
            
        value.set_value(request.params.get(self.field_id(), ''))
        session.add(value)

register_widget(ParagraphTextWidget, ParagraphTextController)
