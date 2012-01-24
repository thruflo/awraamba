import getpass
import logging
import sys
import transaction

from os.path import basename, join as join_path

from pyramid.paster import get_appsettings, setup_logging
from sqlalchemy import engine_from_config
from sqlalchemy.exc import IntegrityError

from ..model import *

def usage(argv):
    """Print usage instructions and exit."""
    
    cmd = basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd)) 
    sys.exit(1)

def setup(argv=sys.argv):
    """Each method below calls ``setup()`` to bind the db session
      to the engine specified in the paste config file provided as the first
      argument on the command line.
    """
    
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    Session.configure(bind=engine)
    return settings, engine


def reset():
    """ Drop all and create afresh.
    """
    
    settings, engine = setup()
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

def create_admin():
    """ Create an admin user.
    """
    
    from ..schema import EncryptedPassword
    
    settings, engine = setup()
    username = unicode(raw_input('Admin username: ') or u'thruflo')
    email = unicode(raw_input('Email address: ') or u'thruflo+spam@gmail.com')
    password = unicode(EncryptedPassword.to_python(getpass.getpass()))
    with transaction.manager:
        user = User.create(username, email, password)
        user.is_admin = True
        user.is_confirmed = True
        Session.add(user)
    

def populate():
    """ Populate the database.
    """
    
    import yaml
    
    settings, engine = setup()
    data = {}
    item_types = ('themes', 'locations', 'characters')
    def _get_model_cls(item_type):
        if item_type == 'themes':
            return Theme
        elif item_type == 'locations':
            return Location
        elif item_type == 'characters':
            return Character
    
    for item in item_types:
        sock = open(join_path(settings['fixtures_dir'], '%s.yaml' % item), 'r')
        data[item] = yaml.load(sock)
        sock.close()
    for k, v in data.iteritems():
        with transaction.manager:
            entities = []
            model_cls = _get_model_cls(k)
            for item in v[k]:
                kwargs = item.copy()
                kwargs['slug'] = kwargs.pop('value')
                # Normalise for strings that are wrapped with double quotes
                # and / or need to have whitespace stripped.
                for j, w in kwargs.items():
                    if isinstance(w, basestring):
                        w = w.strip()
                        if w.startswith('"') and w.endswith('"'):
                            w = w[1:-1]
                        kwargs[j] = w
                # Setup any relations by finding the related entity by type and slug.
                for t in item_types:
                    try:
                        relation_slugs = kwargs.pop(t)
                    except KeyError:
                        pass
                    else:
                        relation_cls = _get_model_cls(t)
                        relations = []
                        for item_ in relation_slugs:
                            relation = relation_cls.get_by_slug(item_)
                            relations.append(relation)
                        kwargs[t] = relations
                entity = model_cls(**kwargs)
                entities.append(entity)
            logging.info('Adding %d %s.' % (len(entities), k))
            Session.add_all(entities)
            transaction.commit()
        
    

def bootstrap():
    """Populate the database from scratch."""
    
    reset()
    create_admin()
    populate()
    

