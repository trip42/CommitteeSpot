from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.decorator import reify
from pyramid.request import Request
from pyramid.url import route_url

from cspot.auth import authenticated_user

from cgi import escape

def js_escape(text):
    return text.replace("'","\\'").replace('"','\\"')

def test(c, t, f):
    if c:
        return t
    else:
        return f

def newline_to_br(text):
   return escape(text).replace('\n','<br>\n') 

@subscriber(BeforeRender)
def add_render_globals(event):
    event['js_escape'] = js_escape
    event['route_url'] = route_url
    event['test'] = test
    event['newline_to_br'] = newline_to_br

class RequestWithUser(Request):
    @reify
    def user(self):
        return authenticated_user(self)
