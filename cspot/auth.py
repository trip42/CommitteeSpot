from cspot.models import DBSession
from cspot.models.users import User
from pyramid.security import authenticated_userid

from pyramid.security import (
        Allow,
        Everyone,
        Authenticated
    )

def root_factory(request):
    class Root:
        __acl__ = [
            (Allow, Everyone, 'view'),
            (Allow, Authenticated, 'view_restricted'),
        ]

        def get_user_roles(self, user_id):
            return []

    return Root()

def get_user(user_id=None, email=None):
    session = DBSession()

    if user_id:
        return session.query(User).filter_by(id=user_id).first()
    elif email:
        return session.query(User).filter_by(email=email.lower()).first()
    else:
        return None

def get_temp_user():
    session = DBSession()

    user = User('', 'Unsaved Project', '')
    session.add(user)
    session.flush()

    return user

def authenticated_user(request):
    user_id = authenticated_userid(request)
    return get_user(user_id=user_id)

def role_finder(user_id, request):
    if request.context is not None:
        return request.context.get_user_roles(get_user(user_id))
    else:
        return []
