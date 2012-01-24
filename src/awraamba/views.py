#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""``RequestHandler``s."""

#import datetime
import formencode
import logging
#import urllib

#from pyramid.response import Response
from pyramid.events import subscriber, NewResponse
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound, HTTPForbidden
from pyramid.view import view_config, view_defaults
from pyramid.security import unauthenticated_userid
from pyramid_weblayer.view import BaseView

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
    


@view_config(route_name='reactions', renderer='json', attr='__call__')
class ReactionsView(BaseView):
    """Reactions container."""
    
    # permission='authenticated'
    def post(self):
        """Create a new reaction."""
        
        p = self.request.params
        data = {
            'theme_slug': p.get('theme_slug'),
            'current_time': p.get('current_time'),
            'url': p.get('url'),
            'message': p.get('message')
        }
        try:
            data = schema.AddReaction.to_python(data)
        except formencode.Invalid as err:
            logging.warning(err)
            self.request.response.status = 400
            return err.unpack_errors()
        else:
            theme = model.Theme.get_by_slug(data['theme_slug'])
            if theme is None:
                raise HTTPNotFound
            data.pop('theme_slug')
            data['theme_id'] = theme.id
            data['user_id'] = self.request.user.id,
            reaction = model.Reaction(**data)
            model.Session.add(reaction)
            return {}
    
    def get(self):
        """Return a list of reactions for the context provided."""
        
        p = self.request.params
        data = {
            'context_type': p.get('context_type'),
            'context_id': p.get('context_id')
        }
        try:
            data = schema.ContextData.to_python(data)
        except formencode.Invalid as err:
            logging.warning(err)
            raise HTTPBadRequest
        else:
            context_cls = getattr(model, data['context_type'].title())
            context = context_cls.get_by_id(data['context_id'])
            return context.reactions
        
    


def not_found_view(context, request):
    return HTTPNotFound('404')

