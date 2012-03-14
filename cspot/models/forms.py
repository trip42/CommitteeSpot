from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from sqlalchemy import Boolean
from sqlalchemy import LargeBinary
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy import CheckConstraint

from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref

from datetime import datetime

from pyramid.security import Allow

from cspot.models import Base

import simplejson


class Form(Base):
    __tablename__ = 'forms'
    id = Column(Integer, primary_key=True)
    type = Column(String(16), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project')

    def __init__(self, project, type):
        self.project = project
        self.type = type
 
class Widget(Base):
    __tablename__ = 'widgets'

    id = Column(Integer, primary_key=True)
    sort_order = Column(Integer)

    form_id = Column(Integer, ForeignKey('forms.id'))
    form = relationship(Form, backref=backref('widgets', order_by=sort_order))
    
    type = Column(String(32), nullable=False)
    label = Column(Unicode(500), nullable=False)
    description = Column(UnicodeText())
    admin_only = Column(Boolean)

    __mapper_args__ = {'polymorphic_on': type}

    def __init__(self, form, label):
        self.form = form
        self.label = label
        self.sort_order = len(form.widgets) + 1
        self.admin_only = False

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
       
class FileUploadWidget(Widget):
    widget_type = 'file_upload'
    name = 'File Upload'

    __mapper_args__ = {'polymorphic_identity':widget_type}


