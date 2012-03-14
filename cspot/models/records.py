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
from cspot.models.users import User

import simplejson

class RecordSet(Base):
    """
    A collection of record values
    """

    __tablename__ = 'record_sets'

    id = Column(Integer, primary_key=True)

class Record(Base):
    """
    A collection or widget values which 
    constitutes a single record. Records are used
    to store values from Forms
    """

    __tablename__ = 'records'

    id = Column(Integer, primary_key=True)

    record_set_id = Column(Integer, ForeignKey('record_sets.id'))
    record_set = relationship(RecordSet, backref=backref('records'))

    def __init__(self, record_set):
        self.record_set = record_set

class ItemRecord(Record):
    title = Column(Unicode(500), nullable=False)

    def __init__(self, record_set, title):
        Record.__init__(self, record_set)
        self.title = title

class FeedbackRecord(Record):
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User, backref=backref('feedback'))

    item_id = Column(Integer, ForeignKey('records.id'))
    item = relationship(ItemRecord, backref=backref('feedback'), remote_side=[ItemRecord.id])

    submitted_on = Column(DateTime)

