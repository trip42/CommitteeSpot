import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import get_appsettings, setup_logging
from ..models import DBSession

def main(argv=sys.argv):
    if len(argv) != 2:
        print "error"
        sys.exit(1)

    config_uri = argv[1]
    setup_logging(config_uri)

    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    
    DBSession.configure(bind=engine)

    Base.metadata.create_all(engine)


