#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""``RequestHandler``s."""

#import datetime
#import formencode
import logging
#import urllib

#from pyramid.response import Response
from pyramid.events import subscriber, NewResponse
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config, view_defaults
from pyramid.security import unauthenticated_userid
from pyramid_weblayer.view import BaseView
#from webob.exc import status_map, HTTPBadRequest, HTTPNotFound, HTTPForbidden

from .mail import PostmarkMailer
from awraamba import model, schema

def get_is_authenticated(request):
    """Get the user for the request."""
    
    user_id = unauthenticated_userid(request)
    unauthenticated = user_id is None
    return not unauthenticated

def get_user(request):
    """Get the user for the request."""
    
    user_id = unauthenticated_userid(request)
    if user_id is not None:
        return model.User.get_by_id(user_id)


@subscriber(NewResponse)
def add_visited_cookie(event):
    """Add a ``visited`` cookie (that lasts for six weeks) to all responses."""
    
    event.response.set_cookie('visited', 'true', max_age=3628800)


@view_defaults(route_name='app')
class AppView(BaseView):
    """Render the main client application."""
    
    @view_config(renderer='app.mako')
    def get(self):
        is_first_time = not self.request.cookies.get('visited', False)
        return {'is_first_time': is_first_time}
    


def not_found_view(context, request):
    return HTTPNotFound('404')

