#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides ``factory``, a WSGI application factory entry point."""

import logging
from os.path import join as join_path

from weblayer.component import registry
from weblayer.interfaces import IPathRouter
from weblayer.route import RegExpPathRouter

from weblayer import Bootstrapper, WSGIApplication

from asset import ManifestedStaticURLGenerator
from auth import SecureCookieAuthenticationManager

try:
    from weblayer.utils import json_decode
except ImportError:
    from json import loads as json_decode

def _convert_list(value, default=None):
    """ Converts value to ``[...]`` if appropriate."""
    
    if value.startswith('[') and value.endswith(']'):
        value = value.replace(', ', ',')
        value = value[1:-1].split(',')
    
    return value
    

def _convert_bool(value, default=None):
    """ Converts value to either `True` or `False`.
      
      Things that are meant to represent true come out `True`::
      
          >>> for value in [
          ...         True, 
          ...         'TRUE', 
          ...         'True', 
          ...         'true', 
          ...         'yes',
          ...         'YES',
          ...         'on', 
          ...         'ON'
          ...     ]:
          ...     _convert_bool(value)
          ... 
          True
          True
          True
          True
          True
          True
          True
          True
      
      And things meant to represent false come out `False`::
      
          >>> for value in [
          ...         False, 
          ...         'FALSE', 
          ...         'False', 
          ...         'false', 
          ...         'no',
          ...         'NO',
          ...         'off', 
          ...         'OFF'
          ...     ]:
          ...     _convert_bool(value)
          ... 
          False
          False
          False
          False
          False
          False
          False
          False
      
      Random shit comes out left alone::
      
          >>> _as_bool('foo')
          'foo'
      
      Unless a `default` is passed in, which is coerced to a `bool`::
      
          >>> _as_bool('foo', default='fandango')
          True
      
    """
    
    if default is not None:
        result = bool(default)
    else:
        result = value
    
    if value in [
            True, 
            'TRUE', 
            'True', 
            'true', 
            'yes',
            'YES',
            'on', 
            'ON' 
        ]:
        result = True
    elif value in [
            False, 
            'FALSE', 
            'False', 
            'false', 
            'no',
            'NO',
            'off', 
            'OFF'
        ]:
        result = False
    
    return result
    

def _parse_config(global_config, local_conf):
    """ Merges a copy of global and local configs into a single dict
      and returns the merged dict::
      
          >>> g = {'debug': True, 'dev_mode': False}
          >>> l = {'shell': False}
          >>> _parse_config(g, l)
          {'debug': True, 'dev_mode': False, 'shell': False}
      
      Converting any strings representing boolean values::
      
          >>> g = {'debug': 'yes', 'dev_mode': 'false'}
          >>> l = {'foo': 'bar'}
          >>> _parse_config(g, l)
          {'debug': True, 'dev_mode': False, 'foo': 'bar'}
      
      Without changing the original config dicts::
      
          >>> g
          {'debug': 'yes', 'dev_mode': 'false'}
          >>> l
          {'foo': 'bar'}
      
    """
    
    config = local_conf.copy()
    config.update(global_config)
    
    for k, v in config.items():
        config[k] = _convert_bool(_convert_list(v))
    
    return config
    

def _get_data(filename, directory=None):
    if directory is None:
        directory = dirname(__file__)
    file_path = join_path(directory, filename)
    try:
        sock = open(file_path)
    except IOError:
        data = None
    else:
        data = json_decode(sock.read())
        sock.close()
    return data
    


def factory(global_config={}, **local_conf):
    """Call with configuration to get a WSGI application."""
    
    # merge the global and local config
    config = _parse_config(global_config, local_conf)
    
    locale_dir = config['locale_directory']
    static_dir = config['static_files_path']
    config['js_message_strings'] = _get_data('message_strings.json', locale_dir)
    config['assetgen_manifest'] = _get_data('assets.json', static_dir)
    
    # setup logging
    log_level = getattr(logging, config['log_level'].upper())
    logging.basicConfig(level=log_level)
    
    # register the components aside from the ``path_router``, because
    # registering a ``path_router`` means importing ``model`` and importing
    # ``model`` requires a registered ``ISettings`` component already
    bootstrapper = Bootstrapper(settings=config)
    settings, path_router = bootstrapper(
        path_router=object(),
        AuthenticationManager=SecureCookieAuthenticationManager,
        StaticURLGenerator=ManifestedStaticURLGenerator
    )
    
    # now we can do stuff which imports model, starting by importing the
    # url mapping to use when registering a path router
    from routes import mapping
    path_router = RegExpPathRouter(mapping)
    registry.registerUtility(path_router, IPathRouter)
    
    # if rebuilding the db from scratch, now create the initial data
    if config.has_key('bootstrap_db'):
        import model
        model.bootstrap()
    elif config.has_key('reset_db'):
        import model
        model.reset_db()
    # if requested, create an admin user.
    elif config.has_key('create_admin'):
        import model
        model.create_admin()
    
    # if requested, enter an interactive shell
    if config.has_key('shell'):
        import code
        code.interact()
    
    # return a wsgi app
    return WSGIApplication(settings, path_router)
    

