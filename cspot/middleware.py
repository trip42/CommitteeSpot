from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.decorator import reify
from pyramid.request import Request
from pyramid.url import route_url

from cspot.auth import authenticated_user

def js_escape(text):
    return text.replace("'","\\'").replace('"','\\"')

def test(c, t, f):
    if c:
        return t
    else:
        return f

@subscriber(BeforeRender)
def add_render_globals(event):
    event['js_escape'] = js_escape
    event['route_url'] = route_url
    event['test'] = test

class RequestWithUser(Request):
    @reify
    def user(self):
        return authenticated_user(self)
