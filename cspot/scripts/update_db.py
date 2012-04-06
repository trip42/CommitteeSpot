import transaction

from sqlalchemy import engine_from_config
from zope.sqlalchemy import mark_changed

from pyramid.paster import bootstrap
from paste.deploy import appconfig

from cspot.models import DBSession
from cspot.models import Base

import simplejson

def main():
    conf = appconfig('config:/home/cspot/webapps/cspot/cspot/production.ini', name='main')
    engine = engine_from_config(conf, 'sqlalchemy.')

    DBSession.configure(bind=engine)
    session = DBSession()
    conn = session.connection()

    # conn.execute('alter table projects add reviewed')

    files = conn.execute("select id, filename from `values` where type = 'file'")

    for id, filename in files.fetchall():
        if filename:
            files = [filename]
        else:
            files = []

        conn.execute("update `values` set text_value = %s where id = %s", simplejson.dumps(files), id)
        print id, files

    mark_changed(session)
    transaction.commit()
 
if __name__ == '__main__':
    main()


