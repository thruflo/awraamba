#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides model classes derived from `SQLAlchemy`_ in `declarative`_ mode.
  
  Note that there *must* be a ``weblayer.interfaces.ISettings`` instance
  registered before importing this module.
  
  .. _SQLAlchemy: http://www.sqlalchemy.org/
  .. _declarative: http://www.sqlalchemy.org/docs/reference/ext/declarative.html
"""

__all__ = [
    'Character',
    'Location',
    'Reaction',
    'Session',
    'Theme',
    'User',
]

import getpass
import logging

from sqlalchemy import desc, event
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy import Boolean, Integer, Unicode, UnicodeText
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from basemodel import engine, Session, SQLModel
from basemodel import AuthMixin, BaseMixin, SearchMixin, SlugMixin

t_reacts = Table(
    't_reacts',
    SQLModel.metadata,
    Column('theme_id', Integer, ForeignKey('themes.id')),
    Column('reaction_id', Integer, ForeignKey('reactions.id'))
)
t_chars = Table(
    't_chars',
    SQLModel.metadata,
    Column('theme_id', Integer, ForeignKey('themes.id')),
    Column('character_id', Integer, ForeignKey('characters.id'))
)
t_locs = Table(
    't_locs',
    SQLModel.metadata,
    Column('theme_id', Integer, ForeignKey('themes.id')),
    Column('location_id', Integer, ForeignKey('locations.id'))
)
c_reacts = Table(
    'c_reacts',
    SQLModel.metadata,
    Column('character_id', Integer, ForeignKey('characters.id')),
    Column('reaction_id', Integer, ForeignKey('reactions.id'))
)
c_locs = Table(
    'c_locs',
    SQLModel.metadata,
    Column('character_id', Integer, ForeignKey('characters.id')),
    Column('location_id', Integer, ForeignKey('locations.id'))
)
l_reacts = Table(
    'l_reacts',
    SQLModel.metadata,
    Column('location_id', Integer, ForeignKey('locations.id')),
    Column('reaction_id', Integer, ForeignKey('reactions.id'))
)

class User(SQLModel, AuthMixin, BaseMixin, SearchMixin):
    """Encapsulates a user."""
    
    __public__ = _search_mapping = ['username', 'name', 'bio']
    
    name = Column(Unicode)
    bio = Column(UnicodeText)
    is_admin = Column(Boolean, default=False)
    
    # Many reactions to one user.
    reactions = relationship("Reaction", backref='user')
    
    @classmethod
    def get_all(cls):
        query = cls.query.order_by(cls.username)
        return query.all()
        
    
    

class Theme(SQLModel, BaseMixin, SearchMixin, SlugMixin):
    """Encapsulates a theme."""
    
    slug = Column(Unicode, unique=True)
    
    title = Column(Unicode)
    description = Column(UnicodeText)
    
    reactions = relationship("Reaction", secondary=t_reacts, backref='themes')
    characters = relationship("Character", secondary=t_chars, backref='themes')
    locations = relationship("Location", secondary=t_locs, backref='themes')
    

class Character(SQLModel, BaseMixin, SearchMixin, SlugMixin):
    """Encapsulates a character.  Has implicit ``themes`` relation set by 
      ``Theme.characters``backref.
    """
    
    slug = Column(Unicode, unique=True)
    
    name = Column(Unicode)
    bio = Column(UnicodeText)
    
    reactions = relationship("Reaction", secondary=c_reacts, backref='characters')
    locations = relationship("Location", secondary=c_locs, backref='characters')
    

class Location(SQLModel, BaseMixin, SearchMixin, SlugMixin):
    """Encapsulates a location.  Has implicit ``themes`` and ``charactera``
      relations set by backref.
    """
    
    slug = Column(Unicode, unique=True)
    
    title = Column(Unicode)
    description = Column(UnicodeText)
    # location = ...
    
    reactions = relationship("Reaction", secondary=l_reacts,  backref='location')
    

class Reaction(SQLModel, BaseMixin, SearchMixin):
    """Encapsulates a user generated comment or external link.  Has implicit
      ``user``, ``themes``, ``characters`` and ``locations`` relations.
      
      ``parent_id`` is set when the reaction is in reply to another reaction.
      ``children`` is a reaction's list of replies.
    """
    
    url = Column(Unicode)
    message = Column(UnicodeText)
    
    user_id = Column(Integer, ForeignKey('users.id'))
    parent_id = Column(Integer, ForeignKey('reactions.id'))
    children = relationship("Reaction", lazy='eager')
    


# bind searchable class create events to ``target._setup_search()``.
for model_class in (Character, Location, Reaction, Theme, User):
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
    

