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
from cspot.models import DBSession
from cspot.models.users import User
from cspot.models.forms import Widget

class Record(Base):
    """
    A collection or widget values which 
    constitutes a single record. Records are used
    to store values from Forms
    """

    __tablename__ = 'records'
    __mapper_args__ = {'polymorphic_on': 'type'}

    id = Column(Integer, primary_key=True)
    type = Column(String(16), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'))

    def __init__(self, project):
        self.project = project

    def get_widget_value(self, widget):
        session = DBSession()
        return session.query(Value).filter(Value.record==self).filter(Value.widget==widget).first()

class ItemRecord(Record):
    __mapper_args__ = {'polymorphic_identity':'item'}

    title = Column(Unicode(500), nullable=False)
    project = relationship('Project', backref='items')

    def __init__(self, project, title):
        Record.__init__(self, project)
        self.title = title

class FeedbackRecord(Record):
    __mapper_args__ = {'polymorphic_identity':'feedback'}

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User, backref=backref('feedback'))

    item_id = Column(Integer, ForeignKey('records.id'))
    item = relationship(ItemRecord, backref=backref('feedback'), remote_side=[ItemRecord.id])

    project = relationship('Project', backref='feedback')

    submitted_on = Column(DateTime)

class Value(Base):
    """
    Stores the value for a single widget
    """

    __tablename__ = 'values'
    __mapper_args__ = {'polymorphic_on': 'type'}

    id = Column(Integer, primary_key=True)
    type = Column(String(16), nullable=False)

    widget_id = Column(Integer, ForeignKey('widgets.id'))
    widget = relationship(Widget, backref=backref('values', cascade='all,delete'))

    record_id = Column(Integer, ForeignKey('records.id'))
    record = relationship(Record, backref=backref('values', cascade='all,delete'))

    def __init__(self, record, widget):
        self.record = record
        self.widget = widget
   

