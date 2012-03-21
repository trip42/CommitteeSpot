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

    def set_filename(self, filename):
        self.filename = filename

    def set_file(self, file):
        open(self.file_path(), 'wb').write(file.read())

    def get_file(self):
        return open(self.file_path(), 'rb').read()


class FileUploadWidgetController(IWidgetController):
    def options(self, request):    
        return render(
            'file_upload_options.pt',
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
            'file_upload.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
                value=value,
            ),
            request
        )

    def render_value(self, value, request):
        return render(
            'file_upload_value.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
                value=value,
            ),
            request
        )

    def render_feedback_summary(self, values, request):
        return render(
            'file_upload_summary.pt',
            dict(
                widget=self.widget,
                field_id=self.field_id(),
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
        return value.filename

    def download(self, value, request):
        from mimetypes import guess_type
        content_type, encoding = guess_type(value.filename)
        return Response(content_type=content_type, body=value.get_file())

register_widget(FileUploadWidget, FileUploadWidgetController)
