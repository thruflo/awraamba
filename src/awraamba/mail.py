#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides ``PostmarkMailer`` utility for sending emails.  Instantiate with
  an api_key::
  
      api_key = '...'
      mailer = PostmarkMailer(api_key)
  
  Then fire away::
  
      ok = mailer.send(to='a@b.com', from='a@b.com', subject='a', text_body='b')
  
"""

import postmark

class PostmarkMailer(object):
    """Provides `send()`, a wrapper around `postmark.PMMail.send()` that sets the
      right api key and handles any relevant error.
    """
    
    def __init__(self, api_key, MailClass=postmark.PMMail):
        self._api_key = api_key
        self._MailClass = MailClass
    
    def send(self, **kwargs):
        """Keyword arguments are ``sender``, ``to``, ``cc``, ``bcc``, ``subject``, 
          ``html_body``, ``text_body``, ``custom_headers`` and ``attachments``.
          See ``postmark.PMMail.send.__doc__`` for the formatting / details.
          
          Returns ``True`` if the mail went off OK or the ``PMMailSendException``
          raised if it doesn't.
        """
        
        mailer = self._MailClass(api_key=self._api_key, **kwargs)
        try:
            mailer.send()
        except postmark.PMMailSendException, err:
            return err
        return True
    

