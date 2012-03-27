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

from random import choice
from string import letters, digits
from crypt import crypt
from uuid import uuid4

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)

    email = Column(String(255), nullable=False, unique=True)
    email_change = Column(String(255))
    
    temporary = Column(Boolean, default=0)

    name = Column(Unicode(255))
    password_hash = Column(String(500))
    password_reset_key = Column(String(35))

    max_projects = Column(Integer, default=1, nullable=False)

    creation_date = Column(DateTime())
    last_login = Column(DateTime())

    __acl__ = [
        (Allow, 'owner', 'manage_profile'),
    ]

    def __init__(self, email=None, name='', password=None):
        self.creation_date = datetime.now()

        if not email:
            # If no e-mail is supplied the user
            # is a temporary user object 
            email = 'temp-' + str(uuid4())
            name = 'Temporary User'
            self.temporary = True

        elif email and not name:
            name = email.split('@')[0]

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

    def projects_remaining(self):
        return self.max_projects - len(self.projects('owner'))

    def set_name(self, name):
        self.name = name.strip()

    def set_email(self, email):
        # Update the e-mail address
        self.email = email.lower().strip()
        self.temporary = False

    def set_password(self, password):
        if password:
            salt = choice(letters+digits) + choice(letters+digits)
            self.password_hash = crypt(password, salt)
            self.temporary = False

    def generate_password(self):
        if not self.password_hash:
            password = ''.join([choice(letters+digits) for x in xrange(8)])
            self.set_password(password)

        return password

    def generate_password_reset_key(self):
        # generate a key, include the user id to prevent
        # conflicts. the key is reset on each login.
        key = str(self.id) + ''.join([choice(letters+digits) for x in range(20)])
        self.password_reset_key = key
        return key

    def authenticate(self, password):
        if self.is_temporary():
            return False

        return self.password_hash and self.password_hash == crypt(password, self.password_hash)

    def set_last_login(self):
        self.password_reset_key = ''
        self.last_login = datetime.now()

    def is_temporary(self):
        return self.temporary

