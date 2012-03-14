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
from cspot.models.forms import Form

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), nullable=False)
    item_name = Column(Unicode(50), nullable=False)
    item_plural = Column(Unicode(55), nullable=False)
    creation_date = Column(DateTime(), nullable=False)

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
        self.creation_date = datetime.now()

        session = DBSession()
        session.add(Form(self, 'item'))
        session.add(Form(self, 'feedback'))
       
    @property
    def item_form(self):
        session = DBSession()
        return session.query(Form).filter(Form.project==self).filter(Form.type=='item').first()

    @property
    def feedback_form(self):
        session = DBSession()
        return session.query(Form).filter(Form.project==self).filter(Form.type=='feedback').first()
 
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

    def get_user_roles_string(user):
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

class ProjectUserRole(Base):
    """
    Association between users and projects maintains
    user/project specific information such as the role
    a user has in the context of the project.
    """

    __tablename__ = 'project_users'

    project_id = Column(Integer, ForeignKey('projects.id'), primary_key=True)
    project = relationship(Project, backref='user_roles')

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    user = relationship(User, backref='project_roles')

    role = Column(String(16), default='reviewer')
    CheckConstraint("role in ('owner','administrator','reviewer')")

 
