#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""``RequestHandler``s."""

from __future__ import with_statement

import base64
import cgi
import gettext
import logging
import math
import quopri
import random
import re
import smtplib
import urllib
import urllib2

from datetime import datetime, timedelta

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import formencode
import pytz

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import query as sqlalchemy_query
from sqlalchemy.sql.expression import asc

from passlib.apps import custom_app_context as pwd_context

from webob.exc import status_map, HTTPBadRequest, HTTPNotFound, HTTPForbidden

from weblayer import RequestHandler as BaseRequestHandler
from weblayer.utils import decode_to_unicode, encode_to_utf8, unicode_urlencode
from weblayer.utils import generate_hash, json_decode, json_encode, xhtml_escape

import auth
import model
import schema

def _escape(value):
    """ Patch https://github.com/thruflo/weblayer/issues/8
    """
    
    if value is None:
        value = ''
    
    return decode_to_unicode(xhtml_escape(value))
    


class RequestHandler(BaseRequestHandler):
    """ Adds i18n support to `weblayer.RequestHandler`, providing `self._`
      and passing `_()` through to templates and `self.country_code`.
    """
    
    __all__ = [
        'head', 
        'get', 
        'post', 
        'put', 
        'delete'
    ]
    
    
    def _get_accepted_languages(self):
        """ Return a list of language tags sorted by their "q" values.
        """
        
        # If a override request param is provided, use that and set an
        # override cookie.
        language = self.request.params.get('override_language', None)
        if language is not None:
            self.cookies.set('override_language', language, expires_days=None)
            return [language]
        
        # Otherwise if an override cookie is provided, use that.
        language = self.cookies.get('override_language')
        if language is not None:
            return [language]
        
        # Otherwise use the `Accept-Language` header, sorting by "q" value.
        header = self.request.headers.get('Accept-Language', None)
        if header is None:
            return []
        langs = [v for v in header.split(",") if v]
        qs = []
        for lang in langs:
            pieces = lang.split(";")
            lang, params = pieces[0].strip().lower(), pieces[1:]
            q = 1
            for param in params:
                if '=' not in param:
                    # Malformed request; probably a bot, we'll ignore
                    continue
                lvalue, rvalue = param.split("=")
                lvalue = lvalue.strip().lower()
                rvalue = rvalue.strip()
                if lvalue == "q":
                    q = float(rvalue)
            qs.append((lang, q))
        qs.sort(lambda a, b: -cmp(a[1], b[1]))
        return [lang for (lang, q) in qs]
        
    
    def create_login_url(self, request_path):
        """
        """
        
        login_url = self.settings.get('login_url', '/login')
        delimiter = '?' in login_url and '&' or '?'
        data = unicode_urlencode({'next': request_path})
        return u'%s%s%s' % (login_url, delimiter, data)
        
    
    def get_thumbnail_url(self, digest):
        return '/thumbnails/%s.png' % digest
        
    
    def redirect(self, location, permanent=False, **kwargs):
        """Use ``303`` as temporary redirect, not ``302`` as is the default."""
        
        status = permanent is True and 301 or 303
        ExceptionClass = status_map[status]
        
        kwargs['location'] = location
        exc = ExceptionClass(**kwargs)
        return self.request.get_response(exc)
        
    
    def render(self, tmpl_name, **kwargs):
        """ Pass `settings`, `escape`, `quote`, `is_ajax` and `_` through to
          the template.
        """
        
        requested_with = self.request.headers.get('X-Requested-With', '')
        is_ajax = requested_with.lower() == 'xmlhttprequest'
        is_ssl = self.request.host_url.startswith('https')
        return super(RequestHandler, self).render(
            tmpl_name, 
            settings=self.settings,
            escape=_escape,
            urlencode=unicode_urlencode,
            generate_hash=generate_hash,
            get_thumbnail_url=self.get_thumbnail_url,
            quote=urllib.quote,
            is_ajax=is_ajax,
            is_ssl=is_ssl,
            _=self._, 
            target_language=self.target_language,
            remaining_languages=self.remaining_languages,
            **kwargs
        )
        
    
    def error(self, exception=None, status=500, **kwargs):
        """ Override weblayer default to render error messages using a nice
          template.
        """
        
        status = int(status)
        if exception is None:
            ExceptionClass = status_map[status]
            exception = ExceptionClass(**kwargs)
        logging.warning(exception)
        response = self.request.get_response(exception)
        response.body = self.render(
            'error.tmpl', 
            title=exception.title,
            error=exception.explanation
        )
        return response
        
    
    def __call__(self, *args, **kwargs):
        """Make sure each web request starts fresh with a brand new session.
        """
        
        r = super(RequestHandler, self).__call__(*args, **kwargs)
        model.Session.remove()
        return r
        
    
    def __init__(self, *args, **kwargs):
        super(RequestHandler, self).__init__(*args, **kwargs)
        # provide `self._` and passing `_()` through to templates
        localedir = self.settings.get('locale_directory')
        supported = self.settings.get('supported_languages')
        target = self.settings.get('default_language')
        for item in self._get_accepted_languages():
            # Convert `en-us` to `en`.
            item = item.split('-')[0]
            if item in supported:
                target = item
                break
        translation = gettext.translation(
            'spaces',
            localedir=localedir, 
            languages=[target]
        )
        self._ = translation.ugettext
        self.target_language = target
        remaining = supported[:]
        remaining.remove(target)
        self.remaining_languages = remaining
        # Make formencode play nicely.
        formencode.api.set_stdtranslation(languages=[target])
        # provide `self.country_code` by setting a `country_code` cookie
        cc = self.cookies.get('country_code')
        if cc is None or cc == 'zz':
            cc = self.request.headers.get('X-AppEngine-Country', 'GB').lower()
            self.cookies.set('country_code', cc, expires_days=None)
        self.country_code = cc
        
    
    


class Index(RequestHandler):
    """
    """
    
    def get(self):
        return self.render('index.tmpl')
        
    
    


#class ConfirmationEmailMixin(object):
#    """Provides a ``send_confirm_notification(user)`` method."""
#    
#    def _send(self, recipient, subject, body):
#        """Handles the email message boilerplate."""
#        
#        msg = MIMEMultipart('related')
#        msg.preamble = 'This is a multi-part message in MIME format.'
#        
#        msg['Subject'] = subject
#        msg['From'] = self.settings['site_email_address']
#        msg['To'] = recipient
#        parts = MIMEMultipart('alternative')
#        msg.attach(parts)
#        
#        parts.attach(MIMEText(encode_to_utf8(body), 'plain', 'utf-8'))
#        
#        smtp_domain = self.settings.get('smtp_domain')
#        smtp_username = self.settings.get('smtp_username')
#        smtp_password = self.settings.get('smtp_password')
#        
#        recipients = [recipient]
#        
#        s = smtplib.SMTP(smtp_domain, 587)
#        s.ehlo()
#        s.starttls()
#        s.ehlo()
#        s.login(smtp_username, smtp_password)
#        s.sendmail(smtp_username, recipients, msg.as_string())
#        s.quit()
#        
#        return True
#        
#    
#    def send_confirm_notification(self, user):
#        """Call to send email.  Returns ``True`` if the email is sent."""
#        
#        # Don't send an email to a user who's already confirmed.
#        if user.is_confirmed:
#            return False
#        
#        subject = self._(u'Please confirm your email address to complete your registration.')
#        recipient = user.email_address
#        body = self.render('emails/confirm.tmpl', user=user)
#        return self._send(recipient, subject, body)
#        
#    
#    
#
#class Login(RequestHandler):
#    """Provides a login form and handles login."""
#    
#    def post(self):
#        """Logs a user in by setting the ``user_id`` cookie."""
#        
#        # Validate the user input.
#        params = {
#            'username': self.request.params.get('username', None),
#            'password': self.request.params.get('password', None),
#            'next': self.request.params.get('next', '/')
#        }
#        try:
#            params = schema.Login.to_python(params)
#        except formencode.Invalid, err:
#            logging.warning(err)
#            errors = err.error_dict and err.error_dict or {}
#            message = self._(u'We couldn\'t log you in.')
#            return self.render('login.tmpl', errors=errors, message=message)
#        
#        # Authenticate the user.
#        user = model.User.authenticate(params['username'], params['password'])
#        if not user:
#            message = self._(u'That username and password didn\'t work.')
#            return self.render('login.tmpl', errors={}, message=message)
#        
#        # Set the ``user_id`` cookie.
#        self.response = self.redirect(params['next'])
#        self.cookies.response = self.response
#        self.cookies.set('user_id', str(user.id))
#        return self.response
#        
#    
#    def get(self):
#        return self.render('login.tmpl', errors={}, message=None)
#        
#    
#    
#
#class Signup(RequestHandler, ConfirmationEmailMixin):
#    """Provides a login form and handles login."""
#    
#    def post(self):
#        """Logs a user in by setting the ``user_id`` cookie."""
#        
#        # Validate the user input.
#        p = self.request.params
#        params = {
#            'username': p.get('username', None),
#            'email_address': p.get('email_address', None),
#            'password': p.get('password', None),
#            'confirm': p.get('confirm', None)
#        }
#        try:
#            params = schema.Signup.to_python(params)
#        except formencode.Invalid, err:
#            logging.warning(err)
#            errors = err.error_dict and err.error_dict or {}
#            message = self._(u'We couldn\'t sign you up.')
#            return self.render('signup.tmpl', errors=errors, message=message)
#        
#        # Create the user.
#        session = model.Session()
#        user = model.User.create(
#            params['username'], 
#            params['email_address'], 
#            params['password']
#        )
#        session.add(user)
#        try:
#            session.commit()
#        except IntegrityError, err:
#            logging.error(err)
#            session.rollback()
#            message = self._(u'We couldn\'t sign you up.')
#            return self.render('signup.tmpl', errors={}, message=message)
#        else: # Send the confirm notification
#            if not self.send_confirm_notification(user):
#                logging.error('Could not send email to %s' % user.email_address)
#                session.rollback()
#                message = self._(u'We couldn\'t sign you up.')
#                return self.render('signup.tmpl', errors={}, message=message)
#            # Redirect to thanks.
#            return self.redirect('/thanks/%s' % params['username'])
#        finally:
#            session.close()
#        
#    
#    def get(self):
#        return self.render('signup.tmpl', errors={}, message=None)
#        
#    
#    
#
#class Thanks(RequestHandler, ConfirmationEmailMixin):
#    """
#    """
#    
#    def _get_context(self, username):
#        username = schema.Username.to_python(username)
#        user = model.User.get_by('username', username)
#        if not user:
#            raise HTTPNotFound
#        return user
#        
#    
#    def post(self, username):
#        user = self._get_context(username)
#        if not self.send_confirm_notification(user):
#            logging.error('Could not send email to %s' % user.email_address)
#            message = self._(u'We couldn\'t resend the email.')
#            return self.render('thanks.tmpl', message=message)
#        
#        message = self._(u'Email resent successfully.')
#        return self.render('thanks.tmpl', message=message)
#        
#    
#    def get(self, username):
#        user = self._get_context(username)
#        return self.render('thanks.tmpl', message=None)
#        
#    
#    
#
#class Confirm(RequestHandler):
#    """
#    """
#    
#    def _get_context(self, confirmation_hash):
#        confirmation_hash = schema.ConfirmationHash.to_python(confirmation_hash)
#        user = model.User.get_by('confirmation_hash', confirmation_hash)
#        if not user:
#            raise HTTPNotFound
#        return user
#        
#    
#    def post(self, confirmation_hash):
#        """Set the user to confirmed and log the user in."""
#        
#        # Validate the user input.
#        user = self._get_context(confirmation_hash)
#        params = {
#            'username': self.request.params.get('username', None),
#            'password': self.request.params.get('password', None),
#            'next': '/'
#        }
#        try:
#            params = schema.Login.to_python(params)
#        except formencode.Invalid, err:
#            logging.warning(err)
#            errors = err.error_dict and err.error_dict or {}
#            message = self._(u'We couldn\'t activate your account.')
#            return self.render('confirm.tmpl', user=user, errors={}, message=None)
#        
#        username_ok = params['username'] == user.username
#        password_ok = pwd_context.verify(params['password'], user.password)
#        if not bool(username_ok and password_ok):
#            message = self._(u'We couldn\'t activate your account.')
#            return self.render('confirm.tmpl', user=user, errors={}, message=message)
#        
#        # Activate the user
#        session = model.Session()
#        user.is_confirmed = True
#        session.add(user)
#        try:
#            session.commit()
#        except IntegrityError, err:
#            logging.error(err)
#            session.rollback()
#            message = self._(u'We couldn\'t activate your account.')
#            return self.render('confirm.tmpl', errors={}, message=message)
#        else: # Log the user in.
#            self.response = self.redirect(params['next'])
#            self.cookies.response = self.response
#            self.cookies.set('user_id', str(user.id))
#            return self.response
#        finally:
#            session.close()
#        
#    
#    def get(self, confirmation_hash):
#        user = self._get_context(confirmation_hash)
#        return self.render('confirm.tmpl', user=user, errors={}, message=None)
#        
#    
#    
#
#class Logout(RequestHandler):
#    """Logs a user out by clearing the ``user_id`` cookie."""
#    
#    def get(self):
#        self.response = self.redirect('/')
#        self.cookies.response = self.response
#        self.cookies.delete('user_id')
#        return self.response
#        
#    
#    
#
#

# XXX put this somewhere more obviously configurable.
STATIC_URLS = (
    #'gfx/....png'
)
class ClientStrings(RequestHandler):
    """Return a translated dictionary of message strings using the keys in
      `~/build/i18n/message_strings.json` and an expanded dict of static urls.
    """
    
    def get(self):
        message_strings = {}
        for k in self.settings.get('js_message_strings'):
            message_strings[k] = self._(k)
        static_urls = {}
        for item in STATIC_URLS:
            static_urls[item] = self.static.get_url(item)
        self.response.headers['Content-Type'] = 'text/javascript'
        self.response.charset = 'utf8'
        return u'window.message_strings = %s;window.static_urls = %s' % (
            json_encode(message_strings),
            json_encode(static_urls)
        )
        
    
    


class NotFound(RequestHandler):
    """
    """
    
    def get(self):
        raise HTTPNotFound
        
    
    

