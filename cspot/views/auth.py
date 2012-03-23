from cspot.models import DBSession
from cspot.models.users import User

from cspot.auth import get_user

from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPUnauthorized

from pyramid.security import remember
from pyramid.security import forget

from pyramid.url import route_url
from pyramid.view import view_config

import smtplib

def forbidden(request):
    came_from = request.url

    return dict(
        came_from=came_from
    )

@view_config(route_name='auth:signup', renderer='cspot:templates/auth/login.pt')
def signup(request):
    user = request.user

    if user and not user.is_temporary():
        raise StandardError, "You may not signup while logged in"

    came_from = request.params.get('came_from', request.referer)
    login_url = route_url('auth:login', request)
    signup_url = route_url('auth:signup', request)
    home_url = route_url('home', request)

    if came_from in [login_url, signup_url, home_url]:
        came_from = route_url('project:list', request)

    name = request.params.get('name','')
    email = request.params.get('email','')
    password = request.params.get('password','')
    password_confirm = request.params.get('password_confirm','')

    if request.method == 'POST':
        if not (name and email and password and password_confirm):
            request.session.flash('Oops! Please complete all fields', 'signup_errors')
        elif get_user(email=email):
            request.session.flash('The e-mail address %s is already in use' % email, 'signup_errors')
        elif password != password_confirm:
            request.session.flash('Your passwords did not match', 'signup_errors')
        else:
            if user:
                # user is logged in with a temporary account
                # update the account information to transfer the current
                # project

                user.set_name(name)
                user.set_email(email)
                user.set_password(password)
                location = came_from

            else:
                user = User(email, name, password)
                location = came_from

            session = DBSession()
            session.add(user)
            session.flush()

            headers = remember(request, user.id)

            return HTTPFound(
                location=location,
                headers=headers
            )

    return dict(
        name=name,
        email=email,
        came_from=came_from
    )

@view_config(route_name='auth:login', renderer='cspot:templates/auth/login.pt')
def login(request):
    if request.user and not request.user.is_temporary():
        raise StandardError, "You must logout first"

    came_from = request.params.get('came_from', request.referer)
    login_url = route_url('auth:login', request)
    signup_url = route_url('auth:signup', request)
    home_url = route_url('home', request)
    logout_url = route_url('auth:logout', request)

    if came_from in [login_url, signup_url, home_url, logout_url]:
        came_from = route_url('project:list', request)

    username = request.params.get('username','')
    password = request.params.get('password','')

    if request.method == 'POST':
        user = get_user(email=username)

        if not (username and password):
            request.session.flash('Please provide a username and password', 'login_errors')

        elif user and user.is_temporary():
            request.session.flash('This account is not available for you to use', 'login_errors')

        elif user and user.authenticate(password):
            user.set_last_login()

            if request.user:
                # A temporary user exists in the request
                # copy the temporary user's projects to the new user
    
                for project in request.user.projects():
                    project.remove_user(request.user)
                    project.remove_user(user)
                    project.add_user(user, 'owner')
                    request.session.flash('%s saved' % project.name, 'messages')
    
            headers = remember(request, user.id)
            request.session['logged_in'] = 'logged_in'
    
            return HTTPFound(
                location=came_from,
                headers=headers
            )
    
        else:
            request.session.flash('Incorrect username or password', 'login_errors')

    return dict(
        came_from=came_from,
        username=username,
    )

@view_config(route_name='auth:logout', renderer='cspot:templates/auth/logout.pt')
def logout(request):
  
    if request.user:
        request.session['logged_in'] = ''
        headers = forget(request)

        return HTTPFound(
            location=route_url('auth:logout', request),
            headers=headers
        )

    else:
        return dict()

@view_config(route_name='auth:password', renderer='cspot:templates/auth/password.pt')
def reset_password(request):
    email = request.params.get('username','')

    if request.method == 'POST' and email:
        user = get_user(email=email)

        if not user:
            request.session.flash('No account found for %s' % email, 'errors')
        
        else:
            settings = request.registry.settings
            server = smtplib.SMTP(settings['cspot.email_server'])
            server.login(settings['cspot.email_user'], settings['cspot.email_password'])

            reset_key = user.generate_password_reset_key()

            data = {}
            data['to_address'] = user.email
            data['to_name'] = user.name
            data['reset_url'] = route_url('auth:password:reset', request, password_reset_key=reset_key)

            msg = u"""
To: %(to_address)s
From: CommitteeSpot <team@committeespot.com>
Subject: CommitteeSpot password reset

%(to_name)s,

This e-mail is response to your e-mail password reset request.

If you requested this password change, please set a new password by following the link below:

%(reset_url)s

If you don't want to change your password, just ignore this message.

Thanks,
CommitteeSpot Team
            """ % data

            msg = msg.strip()

            server.sendmail('team@committeespot.com', user.email, msg)
            server.quit()

            request.session.flash('An e-mail has been sent to %s' % user.email, 'messages')

            return HTTPFound(
                location=route_url('auth:password',request)
            )


    return dict()

@view_config(route_name='auth:password:reset', renderer='cspot:templates/auth/password_reset.pt')
def reset_password_key(request):
    password_reset_key = request.matchdict['password_reset_key']

    password = request.params.get('password','')
    password_confirm = request.params.get('password_confirm','')

    if request.method == 'POST':
        user = get_user(password_reset_key=password_reset_key)

        if not password or password != password_confirm:
            request.session.flash('Passwords do not match', 'errors')
        elif user:
            user.set_password(password)
            user.password_reset_key = ''

            headers = remember(request, user.id)

            request.session.flash('Password successfully reset!', 'messages')

            return HTTPFound(
                location=route_url('project:list', request),
                headers=headers
            )

    return dict(
        password_reset_key=password_reset_key
    )


