#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides model classes derived from `SQLAlchemy`_ in `declarative`_ mode.
  
  Note that there *must* be a ``weblayer.interfaces.ISettings`` instance
  registered before importing this module.
  
  .. _SQLAlchemy: http://www.sqlalchemy.org/
  .. _declarative: http://www.sqlalchemy.org/docs/reference/ext/declarative.html
"""

__all__ = [
    'User'
]

import getpass
import logging
import math
import random

from datetime import datetime, timedelta
from os.path import abspath, basename, dirname, join as join_path

from formencode import validators

from sqlalchemy import create_engine, desc, event, func, or_
from sqlalchemy import Table, Column, MetaData, ForeignKey
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, LargeBinary 
from sqlalchemy import PickleType, Unicode, UnicodeText
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy.orm import backref, mapper, relationship, scoped_session
from sqlalchemy.orm import sessionmaker, synonym
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.pool import NullPool

from passlib.apps import custom_app_context as pwd_context

from weblayer.component import registry
from weblayer.interfaces import ISettings
from weblayer.utils import generate_hash

def engine_factory():
    """ Creates the engine specified by the application settings.
    """
    
    settings = registry.getUtility(ISettings)
    
    db_url = 'postgresql://%s:%s@%s:%s/%s' % (
        settings['db_user'],
        settings['db_password'],
        settings['db_host'],
        settings['db_port'],
        settings['db_name']
    )
    return create_engine(
        db_url, 
        max_overflow=100, 
        pool_size=20, 
        pool_recycle=240, 
        pool_timeout=10
    )
    

engine = engine_factory()

Session = scoped_session(sessionmaker(bind=engine))
SQLModel = declarative_base()

#msg_topics = Table(
#    'msg_topics',
#    SQLModel.metadata,
#    Column('message_id', Integer, ForeignKey('messages.id')),
#    Column('topic_id', Integer, ForeignKey('topics.id'))
#)

class BaseMixin(object):
    """Provides ``id``, ``v`` for version, ``c`` for created and ``m`` for
      modified columns and a scoped ``self.query`` property.
    """
    
    id =  Column(Integer, primary_key=True)
    
    v = Column(Integer, default=1)
    c = Column(DateTime, default=datetime.utcnow)
    m = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    query = Session.query_property()
    
    def __json__(self):
        d = {'__name__': self.__class__.__name__.lower()}
        for k in self.__public__:
            v = getattr(self, k)
            if isinstance(v, datetime):
                v = v.isoformat()
            elif hasattr(v, '__json__'):
                v = v.__json__()
            else:
                try:
                    unicode(v)
                except TypeError:
                    continue
            d[k] = v
        return d
        
    
    
    @property
    def __public__(self):
        return self.__table__.c.keys()
        
    
    
    @declared_attr
    def __tablename__(cls):
        return '%ss' % cls.__name__.lower()
        
    
    
    @classmethod
    def get_by_id(cls, id):
        return cls.query.get(id)
        
    
    
    @classmethod
    def get_by(cls, name, value):
        kwargs = {}
        kwargs[name] = value
        query = cls.query.filter_by(**kwargs)
        return query.first()
        
    
    
    def snip(self, name, limit):
        value = getattr(self, name, None)
        if not value:
            return u''
        if len(value) < limit:
            return value
        return u'%s …' % value[:limit]
        
    
    
    def __repr__(self):
        return '<%s id="%s">' % (self.__name__, self.id)
        
    
    

class SearchMixin(object):
    """When bound to the table create event, adds an indexed full text search
      column to the table and provides a ``tsquery(keywords)`` classmethod to
      filter against it.
      
      Subclasses must override ``self._search_mapping`` with a list if property
      names to index, e.g.::
      
          _search_mapping = ['title', 'description']
      
    """
    
    # Subclass should override with a list of property names to index.
    _search_mapping = NotImplemented
    
    @classmethod
    def _setup_search(cls, target, connection, **kwargs):
        """Add a full text search column to target, indexing ``properties``
          for each language in settings['pg_catalogs'].
          
          This increases disk storage size and increases the complexity of
          search queries, in return for fast queries that are more likely
          to match for users using those languages.
          
          It could be that a different strategy should be used for usernames
          topics, etc. than for natural language.  That's outside the scope
          for now though.
        """
        
        settings = registry.getUtility(ISettings)
        pg_catalogs = settings['pg_catalogs'].split(',')
        
        for item in pg_catalogs:
            # Add an indexed external search column.
            cmd1 = 'ALTER TABLE "%s" ADD COLUMN search_vector_%s tsvector' % (
                target.name,
                item
            )
            cmd2 = 'CREATE INDEX "%s_search_index_%s" on "%s" USING gin(search_vector_%s)' % (
                target.name,
                item,
                target.name,
                item
            )
            # Set up the trigger(s) that keep(s) the tsvector column up to date.
            cmd3 = 'CREATE TRIGGER "%s_search_update_%s" BEFORE UPDATE OR INSERT on "%s" FOR EACH ROW EXECUTE PROCEDURE tsvector_update_trigger(search_vector_%s, "pg_catalog.%s", "%s")' % (
                target.name,
                item,
                target.name,
                item,
                item,
                '", "'.join(cls._search_mapping)
            )
            connection.execute(cmd1)
            connection.execute(cmd2)
            connection.execute(cmd3)
        
    
    
    @classmethod
    def tsquery(cls, keywords):
        """Return a full text search clause using the ``keywords`` provided
          that matches any of the search catalogs.
        """
        
        settings = registry.getUtility(ISettings)
        catalogs = settings['pg_catalogs'].split(',')
        
        ts_query = "plainto_tsquery(E'%s')" % keywords.replace("'", "")
        
        clauses = []
        for item in catalogs:
            clause = "%s.search_vector_%s @@ %s" % (cls.__tablename__, item, ts_query)
            clauses.append(clause)
        
        return or_(*clauses)
        
    
    


class User(SQLModel, BaseMixin, SearchMixin):
    """Encapsulates a user."""
    
    __public__ = [
        'username',
        'name',
        'bio'
    ]
    
    _search_mapping = [
        'username', 
        'name', 
        'bio'
    ]
    
    username = Column(Unicode, unique=True)
    email_address = Column(Unicode, unique=True)
    password = Column(Unicode)
    
    name = Column(Unicode)
    bio = Column(Unicode)
    
    is_admin = Column(Boolean, default=False)
    is_confirmed = Column(Boolean, default=False)
    confirmation_hash = Column(Unicode, unique=True)
    
    def __repr__(self):
        return '<User id="%s" username="%s">' % (self.id, self.username)
        
    
    
    @classmethod
    def authenticate(cls, username, raw_password):
        query = cls.query.filter_by(username=username, is_confirmed=True)
        candidate = query.first()
        if candidate and pwd_context.verify(raw_password, candidate.password):
            return candidate
        return None
        
    
    
    @classmethod
    def create(cls, username, email_address, password):
        user = cls(
            username=username, 
            email_address=email_address,
            password = password
        )
        user.confirmation_hash = unicode(generate_hash()[:32])
        return user
        
    
    
    @classmethod
    def get_all(cls):
        query = cls.query.order_by(cls.username)
        return query.all()
        
    
    


# bind searchable class create events to ``target._setup_search()``.
for model_class in (User,):
    event.listen(model_class.__table__, "after_create", model_class._setup_search)

SQLModel.metadata.create_all(engine)

def reset_db():
    """ Drop all and create afresh.
    """
    
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    
    

def create_admin():
    """ Create an admin user.
    """
    
    session = Session()
    
    import schema
    username = unicode(raw_input('Admin username: ') or u'thruflo')
    email = unicode(raw_input('Email address: ') or u'thruflo+spam@gmail.com')
    password = unicode(schema.EncryptedPassword.to_python(getpass.getpass()))
    
    user = User.create(username, email, password)
    user.is_admin = True
    user.is_confirmed = True
    session.add(user)
    
    try:
        session.commit()
    except IntegrityError, err:
        logging.error(err)
        session.rollback()
    finally:
        session.close()
    

def populate_db():
    """ Populate the database.
    """
    
    return NotImplemented
    

def bootstrap():
    """Populate the database from scratch."""
    
    reset_db()
    create_admin()
    populate_db()
    

