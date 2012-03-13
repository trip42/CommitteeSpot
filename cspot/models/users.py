from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from sqlalchemy import Boolean
from sqlalchemy import LargeBinary
from sqlalchemy import DateTime
from sqlalchemy import PickleType
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy import CheckConstraint

from datetime import datetime

from pyramid.security import Allow

from cspot.models import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    name = Column(Unicode(255))
    password_hash = Column(String(500), nullable=False)
    password_default = Column(String(20))

    creation_date = Column(DateTime())
    last_login = Column(DateTime())

    __acl__ = [
        (Allow, 'owner', 'manage_profile'),
    ]

    def __init__(self, email, name='', password=None):
        self.creation_date = datetime.now()

        self.set_name(name)
        self.set_email(email)
        self.set_password(password)

    def __boolean__(self):
        return True

    def __cmp__(self, other):
        return cmp(self.id, other.id)

    def get_user_roles(self, user):
        """
        Returns the role names for a user in the
        context of this user object. Used by the authorization
        policy via role_finder
        """

        if user == self:
            return ['owner']

        return []

    def projects(self, role=None):
        return [r.project for r in self.project_roles]

    def set_name(self, name):
        self.name = name.strip()

    def set_email(self, email):
        self.email = email.lower().strip()

    def set_password(self, password):
        from random import choice
        from string import letters, digits
        from crypt import crypt

        if not password:
            # Set a default password
            password = ''.join([choice(letters+digits) for x in range(8)])
            self.password_default = password

        salt = choice(letters+digits) + choice(letters+digits)
        self.password_hash = crypt(password, salt)

    def authenticate(self, password):
        from crypt import crypt
        return self.password_hash == crypt(password, self.password_hash)

    def set_last_login(self):
        self.last_login = datetime.now()

    def is_temporary(self):
        return len(self.email) == 0

    def authenticated(self):
        return not self.is_temporary()

