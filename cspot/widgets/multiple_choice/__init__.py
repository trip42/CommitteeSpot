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

    def copy_to(self, widget):
        Widget.copy_to(self, widget)
        widget.choices = self.choices

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
            'options.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
            ),
            request
        )

    def process_type_options(self, request):
        choices = request.params.getall('choices')
        label = request.params.get('label',None)

        self.widget.set_choices(choices)
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
                errors=self.errors,
            ),
            request
        )

    def render_value(self, value, request):
        return render(
            'value.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
                value=value,
            ),
            request
        )

    def render_feedback_for_items(self, items, request):
        rows = []

        choices = self.widget.get_choices()
        headers = [''] + choices
        rows.append(headers)

        for item in items:
            item_totals = {}
            for choice in choices:
                item_totals[choice] = {'count':0, 'percent':255}
    
            num_feedback = len(item.feedback)
        
            for feedback in item.feedback:
                value = feedback.get_widget_value(self.widget) 
                choice = value.get_value()
           
                if choice in item_totals: 
                    item_totals[choice]['count'] += 1
                    item_totals[choice]['percent'] = '%d' % (255 - 50 * item_totals[choice]['count']/num_feedback)

            row = [item.title] + [item_totals.get(choice, {'count':0, 'percent':1}) for choice in choices]
            rows.append(row)
 
        return render(
            'feedback_items.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
                rows=rows
            ),
            request
        )

    def render_feedback_for_item(self, item, request):

        choices = self.widget.get_choices()

        data = {}
        for choice in choices:
            data[choice] = {
                'percent':0,
                'count':0,
                'color':128
            }

        num_feedback = len(item.feedback)

        for feedback in item.feedback:
            value = feedback.get_widget_value(self.widget)
            choice = value.get_value()

            if choice in data:
                data[choice]['count'] += 1

        for choice in data:
            if data[choice]['count']:
                data[choice]['percent'] = int(100 * data[choice]['count'] / num_feedback)
                data[choice]['color'] = int(128 - 128 * data[choice]['percent']/100)

        return render(
            'feedback_item.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
                choices=choices,
                data=data
            ),
            request
        )

    def value(self, value):
        return value.get_value()

    def populate_record_from_request(self, record, request):
        session = DBSession()
        value = session.query(MultipleChoiceValue).filter(Value.record==record).filter(Value.widget==self.widget).first()

        if not value:
            value = MultipleChoiceValue(record, self.widget)
            
        value.set_value(request.params.get(self.field_id(), ''))
        session.add(value)

register_widget(MultipleChoiceWidget, MultipleChoiceWidgetController)
