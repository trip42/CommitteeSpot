from cspot.models import DBSession
from cspot.models.users import User
from cspot.models.projects import Project

from cspot.util import plural_to_singular
from cspot.auth import get_temp_user

from pyramid.url import route_url
from pyramid.view import view_config

from pyramid.security import remember

from pyramid.httpexceptions import HTTPFound

def user_factory(request):
    """
    Generate a user from a profile url
    """

    session = DBSession()
    user_id = request.matchdict.get('user_id', None)

    if user_id:
        return session.query(User).filter(User.id==user_id).first()
    else:
        return request.user

    
@view_config(route_name='user:profile', 
             permission='manage_profile',
             renderer='cspot:templates/users/profile.pt')
@view_config(route_name='user:myprofile', 
             permission='manage_profile',
             renderer='cspot:templates/users/profile.pt')
def user_profile(user, request):
    """
    View and edit a user profile
    """

    if request.method == 'POST' and  not user.is_temporary():

        name = request.params.get('name','')
        email = request.params.get('email','')

        if name.strip():
            user.set_name(name)

        if email.strip():
            user.set_email(email)

        password = request.params.get('password','')
        password_confirm = request.params.get('password_confirm','')

        if password.strip():
            if password == password_confirm:
                user.set_password(password)
                request.session.flash('Password updated', 'messages')
            else:
                request.session.flash('Passwords did not match and were not updated', 'errors')

        request.session.flash('User profile updated', 'messages')

        if 'came_from' in request.session:
            came_from = request.session['came_from']

            del request.session['came_from']

            return HTTPFound(
                location=came_from
            )

    return dict(user=user) 
