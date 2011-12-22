"""Provides ``PostmarkMailer`` utility for sending emails."""

import postmark

from weblayer.component import registry
from weblayer.interfaces import ISettings

class PostmarkMailer(object):
    """Provides `send()`, a wrapper around `postmark.PMMail.send()` that sets the
      right api key and handles any relevant error.
    """
    
    def send(self, **kwargs):
        """Keyword arguments are ``sender``, ``to``, ``cc``, ``bcc``, ``subject``, 
          ``html_body``, ``text_body``, ``custom_headers`` and ``attachments``.
          See ``postmark.PMMail.send.__doc__`` for the formatting / details.
          
          Returns ``True`` if the mail went off OK or the ``PMMailSendException``
          raised if it doesn't.
        """
        
        settings = registry.getUtility(ISettings)
        api_key = settings.get('postmark_apikey')
        
        mail = postmark.PMMail(api_key=api_key, **kwargs)
        try:
            mail.send()
        except postmark.PMMailSendException, err:
            return err
        
        return True
        
    
    

