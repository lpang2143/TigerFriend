#!/usr/bin/env python

# --------------------------------------------------------------------
# banned_sql
# --------------------------------------------------------------------

from datetime import datetime, timedelta
from sys import stderr

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import configs
from database import Banned

DATABASE_URL = configs.DATABASE_URL


def is_banned(net_id):
    # connect to database
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        ban = (session.query(Banned)
               .filter(Banned.net_id == net_id)
               .one_or_none())

        session.close()
        engine.dispose()

        if ban is not None:
            ban_time = datetime.strptime(ban.date_unbanned, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            if now < ban_time:
                return True
            else:
                delete_ban(net_id)
                return False
        return False

    except Exception as ex:
        print(ex, file=stderr)
        print("Banned check failed", file=stderr)


def add_ban(banned, time):
    # connect to database
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        ban = (session.query(Banned)
               .filter(Banned.net_id == banned)
               .one_or_none())

        if ban is not None:
            old_time = datetime.strptime(ban.date_unbanned, "%Y-%m-%d %H:%M:%S")
            if old_time < datetime.now():
                old_time = datetime.now()

            ban.date_unbanned = (old_time + timedelta(days=time)).strftime("%Y-%m-%d %H:%M:%S")

        else:
            new_time = (datetime.now() + timedelta(days=time)).strftime("%Y-%m-%d %H:%M:%S")
            new_ban = Banned(net_id=banned, date_unbanned=str(new_time))
            session.add(new_ban)

        session.commit()
        session.close()
        engine.dispose()

    except Exception as ex:
        print(ex, file=stderr)
        print("Banned add failed", file=stderr)


def get_time(net_id):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        ban = (session.query(Banned)
               .filter(Banned.net_id == net_id)
               .one_or_none())

        session.close()
        engine.dispose()

        return ban.date_unbanned

    except Exception as ex:
        print(ex, file=stderr)
        print("Banned add failed", file=stderr)


def delete_ban(net_id):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        (session.query(Banned)
         .filter(Banned.net_id == net_id)
         .delete())

        session.commit()
        session.close()
        engine.dispose()

    except Exception as ex:
        print(ex, file=stderr)
        print("Banned delete failed", file=stderr)
