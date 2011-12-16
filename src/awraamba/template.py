#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weblayer.template import MakoTemplateRenderer

class Renderer(MakoTemplateRenderer):
    """ `Mako <http://www.makotemplates.org/>`_ template renderer that
      caches modules in the ``/tmp/spaces_mako_modules`` directory.
      
      @@ it should not require a subclass to override a param!
    """
    
    def __init__(self, *args, **kwargs):
        # Don't cache modules in a directory.
        kwargs['module_directory'] = '/tmp/spaces_mako_modules'
        super(Renderer, self).__init__(*args, **kwargs)
        
    
    

