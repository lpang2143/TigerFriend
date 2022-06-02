#!/usr/bin/env python

from datetime import datetime
from sys import stderr

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import configs
from database import Chats, Reports

DATABASE_URL = configs.DATABASE_URL


# Report user with given reporter/reported net_id and type and comment
def report_user(reporter, reported, rep_comment):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        chat_id = (session.query(Chats.chat_id)
                   .filter((Chats.net_id1 == reporter) | (Chats.net_id2 == reporter))
                   .filter((Chats.net_id1 == reported) | (Chats.net_id2 == reported))
                   .one_or_none())
        now = str(datetime.now())

        new_report = Reports(report_id=chat_id[0],
                             reporter_net_id=reporter,
                             reported_net_id=reported,
                             comment=rep_comment,
                             date_time=now)

        session.add(new_report)
        session.commit()

        session.close()
        engine.dispose()

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)


def report_exist(chat_id):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        report_id = (session.query(Reports)
                     .filter(Reports.report_id == chat_id)
                     .one_or_none())

        session.close()
        engine.dispose()

        return report_id

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)


def get_all_reports():
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        reports = (session.query(Reports.report_id, Reports.reported_net_id, Reports.comment)
                   .all())

        session.close()
        engine.dispose()

        return reports

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)


def dismiss_report(chat_id):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        session.query(Reports).filter(Reports.report_id == chat_id).delete()
        session.commit()

        session.close()
        engine.dispose()

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)


# unit test
def main():
    report_user('Tester', 'Bully', 'This person was mean to me.')


# -----------------------------------------------------------------------

if __name__ == '__main__':
    main()
