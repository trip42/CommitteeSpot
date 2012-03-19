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

class MultipleChoiceWidget(Widget):
    widget_type = 'multiple_choice'
    name = 'Multiple Choice'

    __mapper_args__ = {'polymorphic_identity':widget_type}

    choices = Column(UnicodeText())
    
    def __init__(self, form, label):
        Widget.__init__(self, form, label)
        self.set_choices(['Choice 1','Choice 2','Choice 3'])

    def get_choices(self):
        return simplejson.loads(self.choices)

    def set_choices(self, choices=[]):
        self.choices = simplejson.dumps(choices)

class MultipleChoiceValue(Value):
    __mapper_args__ = {'polymorphic_identity':'multiple_choice'}

    def set_value(self, selected_choice=''):
        self.text_value = selected_choice 

    def get_value(self):
        return self.text_value

class MultipleChoiceWidgetController(IWidgetController):
    def data(self):
        return dict(
            choices=self.widget.get_choices()
        )

    def options(self, request):
        return render(
            'multiple_choice_options.pt',
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
            'multiple_choice.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
                value=value,
            ),
            request
        )

    def render_value(self, value, request):
        return render(
            'multiple_choice_value.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
                value=value,
            ),
            request
        )

    def render_feedback_summary(self, values, request):
        summary = {}

        for choice in self.widget.get_choices():
            summary[choice] = {'count':0, 'percent':0.0}

        total = 0.0
        for value in values:
            choice = value.get_value()
            if choice in summary:
                summary[choice]['count'] = summary.get(choice,{}).get('count',0) + 1
                total += 1.0

        if total:
            for key in summary:
                summary[key]['percent'] = int(summary[key]['count'] / total * 100.0)
                

        return render(
            'multiple_choice_summary.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
                summary=summary
            ),
            request
        )

    def populate_record_from_request(self, record, request):
        session = DBSession()
        value = session.query(MultipleChoiceValue).filter(Value.record==record).filter(Value.widget==self.widget).first()

        if not value:
            value = MultipleChoiceValue(record, self.widget)
            
        value.set_value(request.params.get(self.field_id(), ''))
        session.add(value)

register_widget(MultipleChoiceWidget, MultipleChoiceWidgetController)
