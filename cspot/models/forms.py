from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey

from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref

from cspot.models import Base
from cspot.widgets import all_widget_types

class Form(Base):
    """
    A collection of widgets
    """
    
    __tablename__ = 'forms'
    __mapper_args__ = {'polymorphic_on': 'type'}

    id = Column(Integer, primary_key=True)
    type = Column(String(16), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'))

    def __init__(self, project):
        self.project = project

    def has_widgets(self):
        return len(self.widgets)

class ItemForm(Form):
    __mapper_args__ = {'polymorphic_identity':'item'}
    project = relationship('Project', backref=backref('item_form', uselist=False))
    
class FeedbackForm(Form):
    __mapper_args__ = {'polymorphic_identity':'feedback'} 
    project = relationship('Project', backref=backref('feedback_form', uselist=False))

class Widget(Base):
    """
    Base class for form widgets
    """
 
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

    def copy_to(self, widget):
        """
        Copy the values of this widget to another widget
        """
        widget.sort_order = self.sort_order
        widget.label = self.label
        widget.description = self.description
        widget.admin_only = self.admin_only

def widget_factory(widget_type):
    """
    Generate a widget model class for a type
    """

    for model, controller in all_widget_types:
        if model.widget_type == widget_type:
            return model

