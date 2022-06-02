#!/usr/bin/env python

# --------------------------------------------------------------------
# admin_sql
# --------------------------------------------------------------------

from sys import stderr

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

import configs
from database import Administrators, Reports, Messages

DATABASE_URL = configs.DATABASE_URL


def is_admin(net_id):
    # connect to database
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        admin = (session.query(Administrators)
                 .filter(Administrators.net_id == net_id)
                 .one_or_none())

        session.close()
        engine.dispose()

        if admin is not None:
            return True
        return False

    except Exception as ex:
        print(ex, file=stderr)
        print("Admin check failed", file=stderr)


# Returns [reported, reportee, type, comment] of a certain report
def get_report(rep_id):
    # connect to database
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        report = (session.query(Reports)
                  .filter(Reports.report_id == rep_id)
                  .one_or_none())

        rep = [report.reported_net_id, report.reporter_net_id, report.comment]

        session.commit()
        session.close()
        engine.dispose()

        return rep

    except Exception as ex:
        print(ex, file=stderr)
        print("Admin check failed", file=stderr)


# get all message history from a given chat_id (w/no updates to is read (for admin))
# net_id not username for sender
def get_message_history(chat_id):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        msgs = (session.query(Messages)
                .filter(Messages.chat_id == chat_id)
                .order_by(desc(Messages.date_time))
                .all())

        msg_history = []
        for msg in msgs:
            sender = msg.sender_id
            msg_history.append((sender, str(msg.message_content), str(msg.date_time)))

        session.commit()
        session.close()
        engine.dispose()

        return msg_history

    except Exception as ex:
        session.close()
        engine.dispose()
        print(ex, file=stderr)
        print("Data base connection failed", file=stderr)
        return "unknown (database connection failed)"


# ----------------------------------------------------------------------

def make_admin(net_id):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        new_admin = Administrators(net_id=net_id)
        session.add(new_admin)
        session.commit()

        session.close()
        engine.dispose()

    except Exception as ex:
        print(ex, file=stderr)
        print("Admin add failed", file=stderr)


# unit test
def main():
    myself = 'collado'
    print(myself + " is admin: " + str(is_admin(myself)))
    not_admin = 'notanadmin'
    print(not_admin + " is admin: " + str(is_admin(not_admin)))


# ----------------------------------------------------------------------


if __name__ == '__main__':
    main()
