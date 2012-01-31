#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""``RequestHandler``s."""

#import datetime
import formencode
import logging
import json
#import urllib

#from pyramid.response import Response
from pyramid.events import subscriber, NewResponse
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound, HTTPForbidden
from pyramid.view import view_config, view_defaults
from pyramid.security import unauthenticated_userid

from pyramid_assetgen import IAssetGenManifest

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


@view_config(route_name='app', renderer='app.mako', request_method='GET')
def app_view(request):
    """Render the main client application."""
    
    # XXX this way of getting the data is a temporary hack only.
    manifest = request.registry.getUtility(IAssetGenManifest, 'awraamba:assets/')
    manifest_data = json.dumps(manifest._data)
    
    is_first_time = not request.cookies.get('visited', False)
    return {'is_first_time': is_first_time, 'manifest_data': manifest_data}


# permission='authenticated'
@view_config(route_name='reactions', renderer='json', request_method='POST')
def post_reaction_view(request):
    """Add a new reaction."""
    
    p = request.params
    data = {
        'theme_slug': p.get('theme_slug'),
        'timecode': p.get('timecode'),
        'url': p.get('url'),
        'message': p.get('message')
    }
    try:
        data = schema.AddReaction.to_python(data)
    except formencode.Invalid as err:
        logging.warning(err)
        request.response.status = 400
        return err.unpack_errors()
    else:
        theme = model.Theme.get_by_slug(data['theme_slug'])
        if theme is None:
            raise HTTPNotFound
        data['user_username'] = request.user.username
        reaction = model.Reaction(**data)
        model.Session.add(reaction)
        return reaction.__json__()


@view_config(route_name='reactions', renderer='json', request_method='GET')
def get_reactions_view(request):
    """Return a list of reactions.  ATM, this is a pretty naive implementation
      that either gets all the reactions for a theme, or all the reactions
      full stop.  That's not really viable in production...
    """
    
    data = {
        'theme_slug': request.params.get('theme_slug', None),
        'by_username': request.params.get('by_username', None)
    }
    try:
        data = schema.ContextData.to_python(data)
    except formencode.Invalid as err:
        logging.warning(err)
        raise HTTPBadRequest
    else:
        if data['theme_slug']:
            theme = model.Theme.get_by_slug(data['theme_slug'])
            if theme is None:
                raise HTTPNotFound
            reactions = theme.reactions
        elif data['by_username']:
            user = model.User.get_by('username', data['by_username'])
            if user is None:
                raise HTTPNotFound
            reactions = user.reactions
        else:
            reactions = model.Reaction.query.all()
        return [item.__json__() for item in reactions]


def not_found_view(context, request):
    return HTTPNotFound('404')

