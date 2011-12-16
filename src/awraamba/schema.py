#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Form schemas for validation."""

import cgi
import hashlib
import logging
import re
import urllib
import urllib2
import urlparse

from cStringIO import StringIO
from os.path import join as join_path, exists as path_exists

import dateutil.parser
import formencode
from formencode import validators
import Image

from passlib.apps import custom_app_context as pwd_context

from weblayer.component import registry
from weblayer.interfaces import ISettings

from model import User

id_pattern = r'\d+'
valid_id = re.compile(r'^%s$' % id_pattern, re.U)

username_pattern = r'[.\w-]{1,32}'
valid_username = re.compile(r'^%s$' % username_pattern, re.U)

password_pattern = r'(.){7,200}'
valid_password = re.compile(r'^%s$' % password_pattern, re.U)

confirmation_hash_pattern = r'[a-z0-9]{32}'
valid_confirmation_hash = re.compile(r'^%s$' % confirmation_hash_pattern, re.U)

def _(msg):
    """Fake _() so babel extracts the message strings."""
    
    return msg
    


class Id(validators.Int):
    """Ids must be valid integers.
    """
    

class Username(validators.UnicodeString):
    """A valid username.
    """
    
    messages = {
        'invalid': _(u'No spaces, no funny chars, upto 32 characters long.')
    }
    
    def _to_python(self, value, state):
        value = super(Username, self)._to_python(value, state)
        return value.strip().lower()
        
    
    
    def validate_python(self, value, state):
        super(Username, self).validate_python(value, state)
        if not valid_username.match(value):
            raise validators.Invalid(
                self.message("invalid", state),
                value,
                state
            )
        
    

class RawPassword(validators.UnicodeString):
    """Validates that the user input matches ``valid_password``.  Note that all
      passwords are forced to lowercase.
    """
    
    messages = {
        'invalid': _(u'Invalid password.  Must be at least seven characters long.')
    }
    
    def _to_python(self, value, state):
        value = super(RawPassword, self)._to_python(value, state)
        return value.strip().lower()
            
        
    
    def validate_python(self, value, state):
        super(RawPassword, self).validate_python(value, state)
        if not valid_password.match(value):
            raise validators.Invalid(
                self.message("invalid", state),
                value,
                state
            )
            
        
    
    

class EncryptedPassword(validators.UnicodeString):
    """Validates that the user input matches ``valid_password`` and converts it
      to an encrypted hash using passlib_.  Note that all passwords are forced 
      to lowercase.
      
      _passlib: http://packages.python.org/passlib
    """
    
    messages = {
        'invalid': _(u'Invalid password.  Must be at least seven characters long.')
    }
    
    def _to_python(self, value, state):
        """We validate before conversion because we can't validate the hash."""
        
        value = super(EncryptedPassword, self)._to_python(value, state)
        if value:
            if not valid_password.match(value):
                return 'invalid'
            v = value.strip().lower()
            h = pwd_context.encrypt(v, scheme="sha512_crypt", rounds=90000)
            return unicode(h)
            
        
    
    def validate_python(self, value, state):
        super(EncryptedPassword, self).validate_python(value, state)
        if value == 'invalid':
            raise validators.Invalid(
                self.message("invalid", state),
                value,
                state
            )
            
        
    
    

class UnicodeEmail(validators.Email):
    """Overwrite ``validators.Email`` with 
      ``validators.UnicodeString``s ``_to_python`` method.
    """
    
    def _to_python(self, value, state):
        if not value:
            return u''
        if isinstance(value, unicode):
            return value
        if not isinstance(value, unicode):
            if hasattr(value, '__unicode__'):
                value = unicode(value)
                return value
            else:
                value = str(value)
        try:
            return unicode(value, self.inputEncoding)
        except UnicodeDecodeError:
            raise validators.Invalid(
                self.message('badEncoding', state), value, state
            )
        except TypeError:
            raise validators.Invalid(
                self.message(
                    'badType', state, type=type(value), value=value
                ), 
                value, state
            )
        
    
    

class UniqueUsername(Username):
    """Courtesy check to see that a username doesn't exist,
      prior to uniqueness being enforced by constraint.
    """
    
    messages = {
        'taken': _(u'Username has already been taken.')
    }
    
    def validate_python(self, value, state):
        super(UniqueUsername, self).validate_python(value, state)
        if User.query.filter_by(username=value).first():
            raise validators.Invalid(
                self.message("taken", state, username=value),
                value, 
                state
            )
        
    
    

class UniqueEmail(UnicodeEmail):
    """Courtesy check to see that a username doesn't exist,
      prior to uniqueness being enforced by constraint.
    """
    
    messages = {
        'taken': _(u'Email address has already been registered.')
    }
    
    def _to_python(self, value, state):
        value = super(UniqueEmail, self)._to_python(value, state)
        return value.strip().lower()
        
    
    
    def validate_python(self, value, state):
        super(UniqueEmail, self).validate_python(value, state)
        if User.query.filter_by(email_address=value).first():
            raise validators.Invalid(
                self.message("taken", state, email_address=value),
                value, 
                state
            )
        
    
    

class RequestPath(validators.UnicodeString):
    """Valid url path."""
    
    messages = {
        'invalid': _(u'Not a valid URL path.')
    }
    
    def _to_python(self, value, state):
        value = super(RequestPath, self)._to_python(value, state)
        return urllib.unquote_plus(value.strip())
        
    
    
    def validate_python(self, value, state):
        super(RequestPath, self).validate_python(value, state)
        path = urlparse.urlparse(value).path
        if path == value and path.startswith('/'):
            pass
        else:
            raise validators.Invalid(
                self.message("invalid", state),
                value,
                state
            )
        
    
    

class ConfirmationHash(validators.UnicodeString):
    """Must be ``[a-z0-9]{32}``.
    """
    
    messages = {
        'invalid': _(u'Invalid confirmation hash.  Did your email programme mangle the link?')
    }
    
    def _to_python(self, value, state):
        value = super(ConfirmationHash, self)._to_python(value, state)
        return value.strip().lower()
        
    
    
    def validate_python(self, value, state):
        super(ConfirmationHash, self).validate_python(value, state)
        if not valid_confirmation_hash.match(value):
            raise validators.Invalid(
                self.message("invalid", state),
                value,
                state
            )
        
    

class ThumbnailImage(validators.UnicodeString):
    """Takes an image upload or an image url and turns it into a digest
      of a png encoded thumbnail.
    """
    
    messages = {
        'invalid': _(u'Could not save image.'),
        'invalid_digest': _(u'Not a valid digest.')
    }
    
    SIZE = (100, 100)
    
    def _to_python(self, value, state):
        """Takes a file or a url and converts to an ``Image`` instance in
          PNG format that has been thumbnailed.
          
          The ``Image`` is then saved into `/static/thumbnails/` using an
          md5 hash as the filename, with the hash returned as the python
          value from this conversion method.
        """
        
        img = None
        if isinstance(value, cgi.FieldStorage):
            img = Image.open(value.file)
        elif isinstance(value, basestring):
            try:
                response = urllib2.urlopen(value)
            except urllib2.URLError, err:
                logging.warning(err)
            else:
                if response.getcode() == 200:
                    img = Image.open(StringIO(response.read()))
        if img:
            try:
                # thumbnail it
                img = img.convert('RGBA')
                img.thumbnail(self.SIZE, Image.ANTIALIAS)
                # save out to a buffer
                buf = StringIO()
                img.save(buf, 'PNG')
            except Exception, err: # XXX <-- nasty
                logging.warning(err, exc_info=True)
                return err
            # get an md5 hash
            digest = hashlib.md5(buf.getvalue()).hexdigest()
            # if ``/var/thumbnails/$digest`` doesnt already exist then save it
            settings = registry.getUtility(ISettings)
            target_dir = settings.get('thumbnails_directory')
            thumbnail_path = join_path(target_dir, '%s.png' % digest)
            if not path_exists(thumbnail_path):
                try:
                    sock = open(thumbnail_path, 'wb')
                    img.save(sock)
                    sock.close()
                except IOError, err:
                    logging.warning(err, exc_info=True)
                    return err
            return digest
        return None
        
    
    
    def validate_python(self, value, state):
        if isinstance(value, Exception):
            raise validators.Invalid(
                self.message("invalid", state),
                value,
                state
            )
        super(ThumbnailImage, self).validate_python(value, state)
        if value and not valid_md5_digest.match(value):
            raise validators.Invalid(
                self.message("invalid_digest", state),
                value,
                state
            )
        
    
    

class DateTimeString(validators.UnicodeString):
    """Takes a datetime string and parses it into a datetime.
    """
    
    messages = {
        'invalid': _(u'Not a valid datetime.'),
    }
    
    def _to_python(self, value, state):
        if value:
            try:
                value = dateutil.parser.parse(value)
            except ValueError, err:
                return err
        return value
        
    
    
    def validate_python(self, value, state):
        super(DateTimeString, self).validate_python(value, state)
        if isinstance(value, Exception):
            raise validators.Invalid(
                self.message("invalid", state),
                value,
                state
            )
        
        
    
    


class PasswordsMatch(validators.FieldsMatch):
    """Tests that the given password fields match.  The first field must be an
      encrypted password, the subsequent fields must be raw passwords.
    """
    
    def validate_python(self, field_dict, state):
        try:
            encrypted_password = field_dict[self.field_names[0]]
        except TypeError: # Generally because field_dict isn't a dict
            raise validators.Invalid(self.message('notDict', state), field_dict, state)
        except KeyError:
            encrypted_password = None
        if encrypted_password:
            errors = {}
            for name in self.field_names[1:]:
                raw_password = field_dict.get(name)
                # Values are validated both before and after conversion, so we check to
                # see if the raw values match or if the raw password can be verified against
                # encrypted one.
                ok = False
                if raw_password == encrypted_password:
                    ok = True
                else:
                    try:
                        ok = pwd_context.verify(raw_password, encrypted_password)
                    except ValueError:
                        pass
                if not ok:
                    errors[name] = self.message('invalidNoMatch', state)
            if errors:
                error_list = errors.items()
                error_list.sort()
                lines = ['%s: %s' % (name, value) for name, value in error_list]
                raise validators.Invalid(
                    '<br>\n'.join(lines),
                    field_dict, 
                    state, 
                    error_dict=errors
                )
            
        
    
    


class Signup(formencode.Schema):
    """Fields to validate on signup."""
    
    username = UniqueUsername(not_empty=True)
    email_address = UniqueEmail(resolve_domain=True, not_empty=True)
    password = EncryptedPassword(not_empty=True)
    confirm = RawPassword(not_empty=True)
    chained_validators = [
        PasswordsMatch(
            'password', 
            'confirm'
        )
    ]
    

class Login(formencode.Schema):
    """Fields to validate on login."""
    
    username = Username(not_empty=True)
    password = RawPassword(not_empty=True)
    next = RequestPath()
    

