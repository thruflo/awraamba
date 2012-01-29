#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides model classes derived from `SQLAlchemy`_ in `declarative`_ mode.
  
  .. _SQLAlchemy: http://www.sqlalchemy.org/
  .. _declarative: http://www.sqlalchemy.org/docs/reference/ext/declarative.html
"""

__all__ = [
    'Character',
    'Location',
    'Reaction',
    'Session',
    'SQLModel',
    'Theme',
    'User',
]

import logging

from sqlalchemy import desc, event
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy import BigInteger, Boolean, Integer, Numeric, Unicode, UnicodeText
from sqlalchemy.orm import backref, relationship

from basemodel import Session, SQLModel
from basemodel import AuthMixin, BaseMixin, SearchMixin, SlugMixin

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
    
    # Many reactions to one theme.
    reactions = relationship("Reaction", backref='theme')
    
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
      ``user``, ``theme``, ``characters`` and ``locations`` relations.
      
      ``parent_id`` is set when the reaction is in reply to another reaction.
      ``children`` is a reaction's list of replies.
    """
    
    
    url = Column(Unicode)
    message = Column(UnicodeText)
    
    theme_id = Column(Integer, ForeignKey('themes.id'))
    timecode = Column(Numeric)
    
    user_id = Column(Integer, ForeignKey('users.id'))
    
    parent_id = Column(Integer, ForeignKey('reactions.id'))
    children = relationship("Reaction", lazy='eager')
    


# bind searchable class create events to ``target._setup_search()``.
for model_class in (Character, Location, Reaction, Theme, User):
    event.listen(model_class.__table__, "after_create", model_class._setup_search)

