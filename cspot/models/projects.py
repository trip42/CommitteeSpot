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
from sqlalchemy import and_

from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy.orm import aliased

from datetime import datetime

from pyramid.security import Allow

from cspot.models import Base
from cspot.models import DBSession
from cspot.models.users import User
from cspot.models.forms import ItemForm
from cspot.models.forms import FeedbackForm
from cspot.models.records import ItemRecord
from cspot.models.records import FeedbackRecord

from uuid import uuid4

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), nullable=False)
    item_name = Column(Unicode(50), nullable=False)
    item_plural = Column(Unicode(55), nullable=False)
    item_label = Column(Unicode(50), nullable=False)
    creation_date = Column(DateTime(), nullable=False)
    collect_code = Column(Unicode(30), nullable=False)

    template = Column(Boolean, default=False)

    __acl__ = [
        (Allow, 'owner', 'manage_project'),
        (Allow, 'administrator', 'manage_project'),

        (Allow, 'owner', 'review_project'),
        (Allow, 'administrator', 'review_project'),
        (Allow, 'reviewer', 'review_project'),
    ]

    def __init__(self, name, item_name, item_plural):
        self.name = name
        self.item_name = item_name
        self.item_plural = item_plural
        self.item_label = u"%s Name or Title" % item_name
        self.collect_code = str(uuid4())
        self.creation_date = datetime.now()

        session = DBSession()

        session.add(ItemForm(self))
        session.add(FeedbackForm(self))

    def copy_to(self, p):
        p.item_name = self.item_name
        p.item_plural = self.item_plural
        p.item_label = self.item_label

    def add_user(self, user, role):
        """
        Add a user to this project with role
        """
        role = ProjectUserRole(project=self, user=user, role=role)

    def remove_user(self, user):
        """
        Remove a user from the project
        """
        session = DBSession()

        roles = session.query(ProjectUserRole).filter(ProjectUserRole.project==self).filter(ProjectUserRole.user==user)

        for role in roles.all():
            session.delete(role)

        session.flush()

    def get_user_roles(self, user):
        """
        Return the role names for a user in the context
        of this project. Used by the authorization policy
        via role_finder
        """
        session = DBSession()

        roles = session.query(ProjectUserRole).filter(ProjectUserRole.project==self).filter(ProjectUserRole.user==user)
            
        return [r.role for r in roles.all()]

    def has_role(self, user, role):
        """
        Check if a user has a role in the context
        of this project.
        """

        return role in self.get_user_roles(user)

    def get_users(self):
        """
        Return user.id, user.name, user.email, user_role.role
        """

        session = DBSession()

        roles = session.query(User.name, User.email, User.id, User.last_login, User.temporary, ProjectUserRole.role).join(ProjectUserRole.user).filter(ProjectUserRole.project==self)

        return roles

    def get_users_by_role(self, role):
        session = DBSession()

        roles = session.query(ProjectUserRole).filter(ProjectUserRole.project==self).filter(ProjectUserRole.role==role)

        return [r.user for r in roles]

    def get_user_roles_string(self, user):
        """
        Return a string showing the roles for a user
        in the context of this project.
        """

        roles = self.get_user_roles(user)

        if roles:
            return ', '.join(roles)
        else:
            return 'n/a'

    def item_plural_short(self, maxlength=12, default='Items'):
        """
        Returns a shortened version of the item plural name
        """

        if len(self.item_plural) <= maxlength:
            return self.item_plural

        item_plural = self.item_plural.split()[-1]
        if len(item_plural):
            return item_plural

        return default

    def item_name_short(self, maxlength=12, default='Item'):
        """
        Returns a shortened version of the item name
        """

        if len(self.item_name) <= maxlength:
            return self.item_name

        item_name = self.item_name.split()[-1]
        if len(item_name):
            return item_name

        return default

    def get_items_for_user_query(self, user):
        Feedback = aliased(FeedbackRecord, name='feedback_records')

        return DBSession().query(
                    ItemRecord.id, 
                    ItemRecord.title, 
                    ItemRecord.distributed, 
                    Feedback.submitted,
                    Feedback.submitted_on,
                    Feedback.user_id,
                    Feedback.id.label('feedback_id')) \
                .filter(ItemRecord.project == self) \
                .filter(ItemRecord.distributed != None) \
                .outerjoin((Feedback, and_(Feedback.item_id==ItemRecord.id, Feedback.type == 'feedback', Feedback.user_id == user.id))) \
                .order_by(Feedback.submitted, ItemRecord.title)

    def get_item_for_user(self, user, item_id):
        return self.get_items_for_user_query(user).filter(ItemRecord.id == item_id).first()

    def get_items_for_user(self, user):
        return self.get_items_for_user_query(user).all()

    def get_item(self, item_id):
        return DBSession().query(ItemRecord) \
                .filter(ItemRecord.project==self) \
                .filter(ItemRecord.id==item_id) \
                .first()

    def get_item_names(self):
        return DBSession().query(ItemRecord.id, ItemRecord.title, ItemRecord.reviewed) \
                .filter(ItemRecord.project==self) \
                .order_by(ItemRecord.title)

    def items_to_distribute(self):
        return DBSession().query(ItemRecord) \
                .filter(ItemRecord.project==self) \
                .filter(ItemRecord.distributed==None) \
                .order_by(ItemRecord.title).all()

    def items_distributed(self):
        return DBSession().query(ItemRecord) \
                .filter(ItemRecord.project==self) \
                .filter(ItemRecord.distributed!=None) \
                .order_by(ItemRecord.distributed).all()

    def num_items(self):
        return DBSession().query(func.count(ItemRecord)) \
                .filter(ItemRecord.project==self) \
                .scalar()

    def is_owner_temporary(self):
        owner = self.get_users_by_role('owner')[0]
        return owner.is_temporary()

class ProjectUserRole(Base):
    """
    Association between users and projects maintains
    user/project specific information such as the role
    a user has in the context of the project.
    """

    __tablename__ = 'project_users'

    project_id = Column(Integer, ForeignKey('projects.id'), primary_key=True)
    project = relationship(Project, backref=backref('user_roles', cascade='all,delete'))

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    user = relationship(User, backref='project_roles')

    role = Column(String(16), default='reviewer')
    CheckConstraint("role in ('owner','administrator','reviewer')")

 
