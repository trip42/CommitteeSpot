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

    def process_options(self, request):
        label = request.params.get('label',None)
        self.widget.label = label
        session = DBSession()
        session.add(self.widget)

    def render(self, value, request):
        return render(
            'widget.pt',
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

    def populate_record_from_request(self, record, request):
        session = DBSession()
        value = session.query(SingleLineTextValue).filter(Value.record==record).filter(Value.widget==self.widget).first()

        if not value:
            value = SingleLineTextValue(record, self.widget)
            
        value.set_value(request.params.get(self.field_id(), ''))
        session.add(value)

register_widget(SingleLineTextWidget, SingleLineTextController)
