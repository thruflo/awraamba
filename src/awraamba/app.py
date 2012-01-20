#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides a WSGI application ``factory`` function that can be used as an
  setuptools entry point, e.g.::
  
      [paste.app_factory]
      main = %(pkg)s.app:factory
  
"""

from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from pyramid.request import Request
from pyramid_assetgen import AssetGenRequestMixin
from pyramid_beaker import session_factory_from_settings

from .model import Session

# Mapping of route names to patterns.
route_mapping = {
    'explore': '/'
}

def factory(global_config, **settings):
    """Call to return a WSGI application."""
    
    # Bind the SQLAlchemy model classes to the database specified in the
    # ``settings`` provided.
    engine = engine_from_config(settings, 'sqlalchemy.')
    Session.configure(bind=engine)
    
    # Include and configure external libraries.
    config = Configurator(settings=settings)
    config.include('pyramid_assetgen')
    config.include('pyramid_weblayer')
    
    # Setup request and session factories.
    class CustomRequest(AssetGenRequestMixin, Request):
        pass
    
    config.set_request_factory(CustomRequest)
    config.set_session_factory(session_factory_from_settings(settings))
    
    # Tell the translation machinery where the message strings are.
    config.add_translation_dirs(settings['locale_dir'])
    
    # Expose static directories, cached for two weeks, specifying that
    # ``settings['static_dir'] has an assetgen manifest in it.
    static_dir = settings['static_dir']
    thumbs_dir = settings['thumbnails_dir']
    config.add_assetgen_manifest(static_dir)
    config.add_static_view('static', static_dir, cache_max_age=1209600)
    config.add_static_view('thumbs', thumbs_dir, cache_max_age=1209600)
    
    # Expose dynamic views.
    for name, pattern in route_mapping.items():
        config.add_route(name, pattern)
    
    # Run a venusian scan to pick up the declerative configuration from this
    # and any included packages.
    config.scan()
    
    # Return a configured WSGI application.
    return config.make_wsgi_app()

