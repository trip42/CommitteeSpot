from sqlalchemy import Column
from sqlalchemy import Unicode

from pyramid.threadlocal import get_current_registry

from cspot.models import DBSession
from cspot.models.forms import Widget
from cspot.models.records import Value

from cspot.views.forms import IWidgetController

from cspot.widgets import register_widget

from pyramid.renderers import render
from pyramid.response import Response

import mimetypes, os

class FileUploadWidget(Widget):
    widget_type = 'file_upload'
    name = 'File Upload'

    __mapper_args__ = {'polymorphic_identity':widget_type}

class FileUploadValue(Value):
    __mapper_args__ = {'polymorphic_identity':'file'}
    filename = Column(Unicode(200))

    def file_path(self):
        settings = get_current_registry().settings
        return "%s/%s" % (settings['cspot.file_storage_root'], self.id)

    def file_type(self):
        type, subtype = mimetypes.guess_type(self.filename)
        return type or ''

    def set_filename(self, filename):
        self.filename = filename

    def set_file(self, file):
        file.seek(0)
        out = open(self.file_path(), 'wb')

        while True:
            data = file.read(4096)
            if not data: break
            out.write(data)

        out.close()

    def get_file(self):
        return open(self.file_path(), 'rb').read()

    def get_image_size(self):
        return '',''

class FileUploadWidgetController(IWidgetController):
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
        values = []

        for feedback in item.feedback:
            value = feedback.get_widget_value(self.widget)

            if value:
                values.append({
                    'reviewer':feedback.user.name,
                    'file_value':value
                })

        return render(
            'feedback_item.pt',
            dict(
                widget=self.widget,
                values=values
            ),
            request
        )

    def populate_record_from_request(self, record, request):
        session = DBSession()
        value = session.query(FileUploadValue).filter(FileUploadValue.record==record).filter(FileUploadValue.widget==self.widget).first()

        if self.field_id() in request.POST and \
           hasattr(request.POST[self.field_id()], 'filename'):

            if not value:
                value = FileUploadValue(record, self.widget)
                session.add(value)
                session.flush()

            filename = request.POST[self.field_id()].filename
            file = request.POST[self.field_id()].file
                
            value.set_filename(filename)
            value.set_file(file)

    def value(self, value):
        if value:
            return value.filename
        else:
            return ''

    def download(self, value, request):
        from mimetypes import guess_type
        content_type, encoding = guess_type(value.filename)

        res = Response(content_type=content_type, conditional_response=True)
        res.app_iter = open(value.file_path(),'rb')
        res.content_length = os.path.getsize(value.file_path())
        res.last_modified = os.path.getmtime(value.file_path())
        res.etag = '%s-%s-%s' % (os.path.getmtime(value.file_path()),
                                 os.path.getsize(value.file_path()),
                                 hash(value.file_path()))

        return res


register_widget(FileUploadWidget, FileUploadWidgetController)
