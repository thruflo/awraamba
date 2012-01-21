#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""``RequestHandler``s."""

#import datetime
#import formencode
#import logging
#import urllib

#from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config, view_defaults
from pyramid_weblayer.view import BaseView
#from webob.exc import status_map, HTTPBadRequest, HTTPNotFound, HTTPForbidden

from .mail import PostmarkMailer
from awraamba import mail, model, schema

@view_defaults(route_name='app')
class AppView(BaseView):
    """Render the main client application."""
    
    @view_config(renderer='app.mako')
    def get(self):
        return {'foo': 'bar'}
    


def not_found_view(context, request):
    return HTTPNotFound('404')

