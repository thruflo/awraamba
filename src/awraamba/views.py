#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""``RequestHandler``s."""

#import datetime
#import formencode
#import logging
#import urllib

#from pyramid.response import Response
from pyramid.view import view_config, view_defaults
from pyramid_weblayer.view import BaseView
#from webob.exc import status_map, HTTPBadRequest, HTTPNotFound, HTTPForbidden

from .mail import PostmarkMailer
from awraamba import mail, model, schema

@view_defaults(route_name='explore')
class Explore(BaseView):
    """Render the illustrated explore panorama."""
    
    @view_config(renderer='explore.mako')
    def get(self):
        return {'foo': 'bar'}
    

