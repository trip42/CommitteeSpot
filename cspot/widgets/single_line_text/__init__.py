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

class SingleLineTextWidget(Widget):
    widget_type = 'single_line_text'
    name = 'Single Line Text'

    __mapper_args__ = {'polymorphic_identity':widget_type}

    def __init__(self, form, label):
        Widget.__init__(self, form, label)

class SingleLineTextValue(Value):
    __mapper_args__ = {'polymorphic_identity':'single_line_text'}

    def set_value(self, value):
        self.text_value = value

    def get_value(self):
        return self.text_value

class SingleLineTextController(IWidgetController):
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
        label = request.params.get('label',None)
        self.widget.label = label
        session = DBSession()
        session.add(self.widget)

    def render(self, value, request):
        if value:
            value = value.get_value()
        else:
            value = ''

        value = request.params.get(self.field_id(), value)

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
        if value:
            value = value.get_value()
        else:
            value = 'n/a'

        import re
        re1='(http)'    # Word 1
        re2='.*?'   # Non-greedy match on filler
        re3='(\\/www\\.youtube\\.com\\/watch)'  # Unix Path 1
        re4='.*?'   # Non-greedy match on filler
        re5='((?:[a-z][a-z]*[0-9]+[a-z0-9]*))'  # Alphanum 1
        
        rg = re.compile(re1+re2+re3+re4+re5,re.IGNORECASE|re.DOTALL)
        m = rg.search(value)
        if m:
            word1=m.group(1)
            unixpath1=m.group(2)
            alphanum1=m.group(3)

            value = """
            <iframe width="100%%" height="300" src="http://www.youtube.com/embed/%s" frameborder="0" allowfullscreen></iframe>
            """ % alphanum1
        else:
            from cgi import escape
            value = escape(value)

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
        summaries = []

        for item in items:
            summary = self.render_feedback_for_item(item, request)
            summaries.append({
                'item':item,
                'summary':summary
            })

        return render(
            'feedback_items.pt',
            dict(
                widget=self.widget,
                summaries=summaries
            ),
            request
        )

    def render_feedback_for_item(self, item, request):
        summaries = []

        for feedback in item.feedback:
            value = feedback.get_widget_value(self.widget)

            if value and value.get_value():
                summaries.append({
                    'reviewer':feedback.user.name,
                    'comment':value.get_value()
                })

        return render(
            'feedback_item.pt',
            dict(
                widget=self.widget,
                summaries=summaries
            ),
            request
        )

    def value(self, value):
        if value:
            return value.get_value()
        else:
            return ''

    def populate_record_from_request(self, record, request):
        session = DBSession()
        value = session.query(SingleLineTextValue).filter(Value.record==record).filter(Value.widget==self.widget).first()

        if not value:
            value = SingleLineTextValue(record, self.widget)
            
        value.set_value(request.params.get(self.field_id(), ''))
        session.add(value)

register_widget(SingleLineTextWidget, SingleLineTextController)
