#!/usr/bin/env python
from sys import stderr

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

import configs
from database import Account, RawData, Messages, Chats, Banned

DATABASE_URL = configs.DATABASE_URL


def api_account_creation(net_id, year, maj, res, user, bio):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        new_account = Account(net_id=net_id,
                              username=user,
                              class_year=year,
                              major=maj,
                              bio_string=bio,
                              res_college=res)

        session.add(new_account)
        session.commit()

        session.close()
        engine.dispose()

    except Exception as ex:
        print(ex, file=stderr)
        print("Account creation failed", file=stderr)


def update_bio(net_id, bio):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        update = (session.query(Account)
                  .filter(Account.net_id == net_id)
                  .one())
        update.bio_string = bio

        session.commit()
        session.close()
        engine.dispose()
        print("Record inserted successfully into account")

    except Exception as ex:
        print(ex, file=stderr)
        print("Update bio failed", file=stderr)


# to get net_id from username
def get_netid(user):
    engine = create_engine(DATABASE_URL)

    Session = sessionmaker(bind=engine)
    session = Session()

    user = (session.query(Account)
            .filter(Account.username == user)
            .all())

    session.close()
    engine.dispose()
    if not user:
        return None
    return user[0].net_id


# to get bio for the chat
def get_bio(username):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        user = (session.query(Account)
                .filter(Account.username == username)
                .all())

        session.close()
        engine.dispose()
        if not user:
            return "No user with this username"
        return user[0].bio_string
    except Exception as ex:
        print(ex, file=stderr)
        print("No user with this username", file=stderr)


# returns year and major & res college
def get_year_major(net_id):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        user = (session.query(Account)
                .filter(Account.net_id == net_id)
                .all())

        session.close()
        engine.dispose()
        if not user:
            return ["unknown (" + net_id + " not found)", "?"]
        return [user[0].class_year, user[0].major, user[0].res_college]
    except Exception as ex:
        print(ex, file=stderr)
        print("Data base connection failed", file=stderr)
        return ["unknown (database connection failed)", "unknown"]


# returns user and bio, None if account doesn't exist
def get_user_bio(net_id):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        user = (session.query(Account)
                .filter(Account.net_id == net_id)
                .all())

        session.close()
        engine.dispose()
        if not user:
            return None
        return [user[0].username, user[0].bio_string]

    except Exception as ex:
        print(ex, file=stderr)
        print("Data base connection failed", file=stderr)
        return ["unknown (database connection failed)", "unknown"]


# adapted from chat_sql.py to avoid circular import
def __get_chat_ids__(user):
    try:
        # connect to database
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        chats = (session.query(Chats).filter((Chats.net_id1 == user) | (Chats.net_id2 == user))
                 .order_by(desc(Chats.latest_date_time))
                 .all())

        chat_ids = []
        for chat in chats:
            chat_ids.append(chat.chat_id)

        session.close()
        engine.dispose()
        return chat_ids

    except Exception as ex:
        session.close()
        engine.dispose()
        print(ex, file=stderr)
        print("Data base connection failed", file=stderr)
        return "unknown (database connection failed)"


# Deletes account associated with net_id and all other info (except admin status)
# Match scores must be deleted in PGAdmin due to SQLAlchemy incompatibility
def clear_account(net_id):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        chat_ids = __get_chat_ids__(net_id)

        for chat in chat_ids:
            (session.query(Messages)
             .filter(Messages.chat_id == chat)
             .delete())

            session.commit()

            (session.query(Chats)
             .filter(Chats.chat_id == chat)
             .delete())

            session.commit()

        # DOESN'T WORK WITH SQLAlchemy; NO PRIMARY KEY IN MATCHSCORES
        # DELETE MATCHSCORES MANUALLY IN PGAdmin using:
        #
        # DELETE FROM public.matchscores
        #     WHERE net_id1 = {{net_id}} OR net_id2 = {{net_id}};
        #
        # (session.query(MatchScores)
        #         .filter((MatchScores.net_id1 == net_id) | (MatchScores.net_id2 == net_id))
        #         .delete())
        # session.commit()

        (session.query(Account)
         .filter(Account.net_id == net_id)
         .delete())

        session.commit()

        (session.query(RawData)
         .filter(RawData.net_id == net_id)
         .delete())

        session.commit()

        (session.query(Banned)
         .filter(Banned.net_id == net_id)
         .delete())

        session.commit()

        (session.query())

        session.close()
        engine.dispose()

    except Exception as ex:
        print(ex, file=stderr)
        print("Data base connection failed", file=stderr)
        return ["unknown (database connection failed)", "unknown"]


# run main to delete user
def main():
    user = 'collado'
    clear_account(user)
    print(user + "'s account was deleted")


# ----------------------------------------------------------------------


if __name__ == '__main__':
    main()
