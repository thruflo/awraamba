#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides a WSGI application ``factory`` function that can be used as an
  setuptools entry point, e.g.::
  
      [paste.app_factory]
      main = %(pkg)s.app:factory
  
"""

from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from pyramid.authentication import RemoteUserAuthenticationPolicy
from pyramid.request import Request
from pyramid.view import AppendSlashNotFoundViewFactory
from pyramid_assetgen import AssetGenRequestMixin
from pyramid_beaker import session_factory_from_settings

from .model import Session
from .views import add_visited_cookie, get_is_authenticated, get_user
from .views import not_found_view

# Mapping of route names to patterns.
route_mapping = (
    ('reactions', '/api/reactions/'),
    ('app', '/*path'),
)

def factory(global_config, **settings):
    """Call to return a WSGI application."""
    
    # Bind the SQLAlchemy model classes to the database specified in the
    # ``settings`` provided.
    engine = engine_from_config(settings, 'sqlalchemy.')
    Session.configure(bind=engine)
    
    # Initialise the ``Configurator`` with authentication policy.
    auth_policy = RemoteUserAuthenticationPolicy()
    config = Configurator(settings=settings, authentication_policy=auth_policy)
    
    # Include external libraries.
    config.include('pyramid_assetgen')
    config.include('pyramid_weblayer')
    
    # Setup request and session factories.
    class CustomRequest(AssetGenRequestMixin, Request):
        pass
    
    config.set_request_factory(CustomRequest)
    config.set_session_factory(session_factory_from_settings(settings))
    
    # Add ``is_authenticated`` and ``user`` properties to the request.
    config.set_request_property(get_is_authenticated, 'is_authenticated', reify=True)
    config.set_request_property(get_user, 'user', reify=True)
    
    # Tell the translation machinery where the message strings are.
    config.add_translation_dirs(settings['locale_dir'])
    
    # Expose `/static` and `/thumbs` directories, cached for two weeks,
    # specifying that ``settings['static_dir'] has an assetgen manifest
    # in it, and expose the panorama `/tour` files without caching.
    static_dir = settings['static_dir']
    thumbs_dir = settings['thumbnails_dir']
    tour_dir = settings['tour_dir']
    config.add_assetgen_manifest(static_dir)
    config.add_static_view('static', static_dir, cache_max_age=1209600)
    config.add_static_view('thumbs', thumbs_dir, cache_max_age=1209600)
    config.add_static_view('tour', tour_dir)
    
    # Configure a custom 404 that first tries to append a slash to the URL.
    not_found = AppendSlashNotFoundViewFactory(not_found_view)
    config.add_view(not_found, context='pyramid.httpexceptions.HTTPNotFound')
    
    # Expose dynamic views.
    for name, pattern in route_mapping:
        config.add_route(name, pattern)
    
    # Run a venusian scan to pick up the declerative configuration from this
    # and any included packages.
    config.scan()
    
    # Fake authentication for now.
    class AuthenticationMiddleware:
        def __init__(self, app):
            self.app = app
        
        def __call__(self, environ, start_response):
            environ['REMOTE_USER'] = '1'
            return self.app(environ, start_response)
        
    
    # Return a configured WSGI application.
    return AuthenticationMiddleware(config.make_wsgi_app())

