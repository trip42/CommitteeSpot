import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import bootstrap
from paste.deploy import appconfig

from cspot.models import DBSession
from cspot.models import Base

from cspot.models.projects import Project
from cspot.models.users import User

def main():
    conf = appconfig('config:/home/cspot/webapps/cspot/cspot/development.ini', name='main')
    engine = engine_from_config(conf, 'sqlalchemy.')

    DBSession.configure(bind=engine)

    Base.metadata.bind = engine
    Base.metadata.bind.echo = True
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    main()


