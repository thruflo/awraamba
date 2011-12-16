#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Provides `@auth.require_login` and `@auth.require_admin` decorators and
  ``SecureCookieAuthenticationManager``, an ``IAuthenticationManager``
  implementation.
"""

import logging

from zope.component import adapts
from zope.interface import implements

from weblayer.component import registry
from weblayer.cookie import SignedSecureCookieWrapper
from weblayer.interfaces import IAuthenticationManager, IRequest, ISettings

class ModelClassFactory(object):
    """Provides a callable that returns ``model`` classes without having to
      import ``model`` at module load time.
    """
    
    _model = None
    
    def __call__(self, name):
        if self._model is None:
            import model
            self._model = model
        return getattr(self._model, name)
        
    
    

modelClassFactory = ModelClassFactory()

def _get_user(user_id):
    User = modelClassFactory('User')
    return User.get_by_id(user_id)
    

def _get_place(place_id):
    Place = modelClassFactory('Place')
    return Place.get_by_id(place_id)
    


def require_login(handler_method):
    """ Decorator to require that a user be logged in to access a handler.
    """
    
    def check(self, *args, **kwargs):
        if self.auth.current_user is None:
            return self.redirect(self.create_login_url(self.request.path))
        return handler_method(self, *args, **kwargs)
        
    
    return check
    

def require_user(handler_method):
    """ Decorator to require that the username passed as first argument to the
      ``handler_method`` belongs to the logged in user.
    """
    
    def check(self, *args, **kwargs):
        if self.auth.current_user is None:
            return self.redirect(self.create_login_url(self.request.path))
        elif not self.auth.current_user.username == args[0]:
            return self.error(status=403)
        return handler_method(self, *args, **kwargs)
        
    
    return check
    

def require_admin(handler_method):
    """ Decorator to require that a user be logged in and an admin.
    """
    
    def check(self, *args, **kwargs):
        if self.auth.current_user is None:
            return self.redirect(self.create_login_url(self.request.path))
        elif not self.auth.current_user.is_admin:
            return self.error(status=403)
        return handler_method(self, *args, **kwargs)
        
    
    
    return check
    

def require_place_creator_or_admin(handler_method):
    """ Decorator to require that a user be logged in and, if there is a place,
      either an admin, or the creator of that place.
      
      Note that if a place_id is provided but the place doesn't exist, this
      decorate allows the method to be called, i.e.: this authentication 
      decorator is only concerned with restricting access if the user isn't
      logged in or shouldn't be entitled to edit an existing place.
    """
    
    def check(self, *args, **kwargs):
        
        # If the user is not logged in, redirect to login.
        if self.auth.current_user is None:
            return self.redirect(self.create_login_url(self.request.path))
        
        # If there is a place and the user is neither an admin nor the places's
        # creator, raise a forbidden error.
        place_id = len(args) and args[0] or None
        if place_id and not self.auth.current_user.is_admin:
            place = _get_place(place_id)
            if place and place.created_by_user_id != self.auth.current_user.id:
                return self.error(status=403)
        
        # Otherwise allow the method to be accessed.
        return handler_method(self, *args, **kwargs)
        
    
    
    return check
    


class SecureCookieAuthenticationManager(object):
    """ Gets the current user from a ``user.id`` in a secure cookie.
    """
    
    adapts(IRequest)
    implements(IAuthenticationManager)
    
    def __init__(self, request):
        """ Laboriously work around the poor design decision to make
          the ``IAuthenticationManager`` component adapt only an ``IRequest``
          and not an ``IRequestHandler``.
        """
        
        settings = registry.getUtility(ISettings)
        
        self.cookies = SignedSecureCookieWrapper(request, None, settings)
        self.request = request
        
    
    
    @property
    def is_authenticated(self):
        return self.current_user is not None
        
    
    
    @property
    def current_user(self):
        """ Lazy load, looking in cookie and db if necessary.
        """
        
        if hasattr(self, '_current_user'):
            return self._current_user
        
        user = None
        user_id = self.cookies.get('user_id')
        
        if user_id:
            user = _get_user(user_id)
            logging.debug(user)
        
        self._current_user = user
        return user
        
    
    


