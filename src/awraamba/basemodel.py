#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Abstracts SQLAlchemy boilerplace away from ``model.py``."""

__all__ = [
    'engine',
    'AuthMixin',
    'BaseMixin',
    'SearchMixin',
    'Session',
    'SlugMixin',
    'SQLModel',
]

import logging
from datetime import datetime

from sqlalchemy import create_engine, desc, or_
from sqlalchemy import Column, MetaData
from sqlalchemy import Boolean, DateTime, Integer, Unicode
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from passlib.apps import custom_app_context as pwd_context

from weblayer.component import registry
from weblayer.interfaces import ISettings
from weblayer.utils import generate_hash

def engine_factory():
    """Creates the engine specified by the application settings."""
    
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

class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()
    


class AuthMixin(object):
    """Provides ``username``, ``email`` and ``password`` properties and 
      `authenticate()` and `create()` classemthods.
    """
    
    username = Column(Unicode, unique=True)
    email = Column(Unicode, unique=True)
    password = Column(Unicode)
    
    is_confirmed = Column(Boolean, default=False)
    confirmation_hash = Column(Unicode, unique=True)
    
    @classmethod
    def authenticate(cls, username, raw_password):
        query = cls.query.filter_by(username=username, is_confirmed=True)
        candidate = query.first()
        if candidate and pwd_context.verify(raw_password, candidate.password):
            return candidate
        return None
        
    
    @classmethod
    def create(cls, username, email, password):
        user = cls(
            username=username, 
            email=email,
            password = password
        )
        user.confirmation_hash = unicode(generate_hash()[:32])
        return user
        
    
    

class BaseMixin(object):
    """Provides ``id``, ``v`` for version, ``c`` for created and ``m`` for
      modified columns and a scoped ``self.query`` property.
    """
    
    id =  Column(Integer, primary_key=True)
    
    v = Column(Integer, default=1)
    c = Column(DateTime, default=datetime.utcnow)
    m = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    query = Session.query_property()
    
    @declared_attr
    def __tablename__(cls):
        return '%ss' % cls.__name__.lower()
        
    
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
        
    
    
    @classmethod
    def get_by_id(cls, id):
        return cls.query.get(id)
        
    
    @classmethod
    def get_by(cls, name, value):
        kwargs = {}
        kwargs[name] = value
        query = cls.query.filter_by(**kwargs)
        return query.first()
        
    
    @classmethod
    def get_all(cls):
        query = cls.query.order_by(cls.c.desc())
        return query.all()
        
    
    
    def snip(self, name, limit):
        value = getattr(self, name, None)
        if not value:
            return u''
        value = unicode(value)
        if len(value) < limit:
            return value
        return u'%s …' % value[:limit]
    
    def __unicode__(self):
        attrs = [u'%s="%s"' % (k, self.snip(k, 50)) for k in self.__public__]
        response = u'<%s %s />' % (self.__class__.__name__, u' '.join(attrs))
        return response
    
    def __repr__(self):
        return repr(unicode(self))
    
    

class SearchMixin(object):
    """When bound to the table create event, adds an indexed full text search
      column to the table and provides a ``tsquery(keywords)`` classmethod to
      filter against it.
      
      The default is to index *all* text / varchar fields (which includes all
      ``Column(Unicode)``s.  Subclasses can override ``self._search_mapping``
      with a list if property names to index, e.g.::
      
          _search_mapping = ['title', 'description']
      
    """
    
    @classmethod
    def get_search_mapping(cls):
        items = []
        fields = cls.__table__.c
        for item in fields.keys():
            if str(fields.get(item).type) in ['VARCHAR', 'TEXT']:
                items.append(item)
        return items
    
    _search_mapping = ClassProperty(get_search_mapping)
    
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
        
    
    

class SlugMixin(object):
    """Provides ``slug`` property and ``get_by_slug`` classmethod.  A "slug" is
      intended to be a short, unique textual identifier (much like a username)
      that can be used in a vanity URL.
      
      For example, we might use the slug "monmouth" when linking to a coffee
      shop called the "Monmouth Street Coffee Company" in a url like 
      ``/shops/coffee/monmouth``.
      
      However, that said, this implementation doesn't prescribe anything other
      than the slug value be a unicode string that is unique.
    """
    
    slug = Column(Unicode, unique=True)
    
    @classmethod
    def get_by_slug(cls, slug):
        return cls.query.filter_by(slug=slug).first()
    

