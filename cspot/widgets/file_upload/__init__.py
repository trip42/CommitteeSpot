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
import simplejson

class FileUploadWidget(Widget):
    widget_type = 'file_upload'
    name = 'File Upload'

    __mapper_args__ = {'polymorphic_identity':widget_type}

class FileUploadValue(Value):
    __mapper_args__ = {'polymorphic_identity':'file'}

    def __init__(self, record, widget):
        Value.__init__(self, record, widget)

        self.set_filenames([])

    def dir_path(self):
        settings = get_current_registry().settings
        dir_path = "%s/%s" % (settings['cspot.file_storage_root'], self.id)

        if not os.access(dir_path, os.F_OK):
            os.mkdir(dir_path)

        return dir_path

    def file_path(self, filename):
        return self.dir_path() + '/' + filename

    def file_type(self, filename):
        type, subtype = mimetypes.guess_type(filename)
        return type or ''

    def add_filename(self, filename):
        filenames = self.get_filenames()
        if filename not in filenames:
            filenames.append(filename)
        self.set_filenames(filenames)

    def set_filenames(self, filenames):
        self.text_value = simplejson.dumps(filenames)

    def get_filenames(self):
        return simplejson.loads(self.text_value)

    def add_file(self, filename, file):
        self.add_filename(filename)

        file.seek(0)
        out = open(self.file_path(filename), 'wb')

        while True:
            data = file.read(4096)
            if not data: break
            out.write(data)

        out.close()

    def get_file(self, filename):
        return open(self.file_path(filename), 'rb').read()

    def get_image_size(self, filename):
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

    def process_type_options(self, request):
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

    def validate_from_request(self, request):
        """
        Validate that an acceptable value was submitted
        """

        filenames = request.POST.getall(self.field_id() + '_filenames')
        files = [file for file in request.POST.getall(self.field_id()) if hasattr(file, 'filename')]
        
        num_files = len(filenames) + len(files)

        if self.widget.required and num_files == 0:
            self.errors.append('You must select at least one file')

        return self.errors

    def populate_record_from_request(self, record, request):
        session = DBSession()
        value = session.query(FileUploadValue).filter(FileUploadValue.record==record).filter(FileUploadValue.widget==self.widget).first()

        if value:
            # Update the filenames based on the filenames
            # included in the request
            # XXX we should remove the files as well
            old_filenames = value.get_filenames()
            new_filenames = request.POST.getall(self.field_id() + '_filenames')

            # remove any filename that wasn't already part
            # of the value
            for filename in new_filenames:
                if filename not in old_filenames:
                    new_filenames.remove(filename)

            value.set_filenames(new_filenames)
    
        if self.field_id() in request.POST:
            for file_upload in request.POST.getall(self.field_id()):
                if hasattr(file_upload, 'filename'):

                    if not value:
                        value = FileUploadValue(record, self.widget)
                        session.add(value)
                        session.flush()

                    filename = file_upload.filename
                    file = file_upload.file
                
                    value.add_file(filename, file)

    def value(self, value):
        if value:
            return ', '.join(self.get_filenames())
        else:
            return ''

    def download(self, value, filename, request):
        from mimetypes import guess_type
        content_type, encoding = guess_type(filename)

        file_path = value.file_path(filename)

        res = Response(content_type=content_type, conditional_response=True)
        res.app_iter = open(file_path,'rb')
        res.content_length = os.path.getsize(file_path)
        res.last_modified = os.path.getmtime(file_path)
        res.etag = '%s-%s-%s' % (os.path.getmtime(file_path),
                                 os.path.getsize(file_path),
                                 hash(file_path))

        return res


register_widget(FileUploadWidget, FileUploadWidgetController)
