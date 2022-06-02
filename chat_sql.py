#!/usr/bin/env python

import random
# --------------------------------------------------------------------
# chat_sql.py
# --------------------------------------------------------------------
from datetime import datetime
from queue import Queue
from sys import stderr

from pytz import timezone
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

import configs
from account_sql import get_user_bio, get_netid
from database import Chats, Account, Messages

DATABASE_URL = configs.DATABASE_URL


# --------------------------------------------------------------------

# Takes user (net_id) and returns a list of chat info for each open chat they have.
# UPDATE: List format = [(chat_id, receiver, is_empty, is_unread), ...]
def get_all_chats(user):
    try:
        # connect to database
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        chats = (session.query(Chats).filter((Chats.net_id1 == user) | (Chats.net_id2 == user))
                 .order_by(desc(Chats.latest_date_time))
                 .all())

        chat_list = []
        q = Queue()
        for chat in chats:
            chat_id = str(chat.chat_id)
            other_id = chat.net_id1
            if other_id == user:
                other_id = chat.net_id2
            receiver = (session.query(Account)
                        .filter(Account.net_id == other_id)
                        .first())
            receiver = str(receiver.username)
            if chat.latest_date_time is None or is_empty(chat_id):
                q.put((chat_id, receiver, is_empty(chat_id), is_unread(chat_id, user)))
            else:
                chat_list.append((chat_id, receiver, is_empty(chat_id), is_unread(chat_id, user)))

        for chat in q.queue:
            chat_list.append(chat)

        session.close()
        engine.dispose()
        return chat_list

    except Exception as ex:
        session.close()
        engine.dispose()
        print(ex, file=stderr)
        print("Data base connection failed", file=stderr)
        return "unknown (database connection failed)"


# Takes user (net_id) and their match (username), and returns their
# chat_id. Makes a new one and inserts if it doesn't exist in the table.
def get_chat_id(user, match):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        matchid = get_netid(match)
        if matchid is None:
            return "No match username found"

        chats = (session.query(Chats)
                 .filter((Chats.net_id1 == user) | (Chats.net_id2 == user))
                 .all())

        chatid = None
        for chat in chats:
            if (str(chat.net_id1) == matchid) | (str(chat.net_id2) == str(matchid)):
                chatid = chat.chat_id
                break
        if chatid is None:
            print("will insert")
            chatid = __insert_chat_id__(user, matchid)

        session.close()
        engine.dispose()
        return chatid

    except Exception as ex:
        session.close()
        engine.dispose()
        print(ex, file=stderr)
        print("Data base connection failed", file=stderr)
        return "unknown (database connection failed)"


# helper method for get_chat_id
def __insert_chat_id__(user, matchid):
    try:
        # connect to database
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        new_id = str(random.randint(1000, 9999))
        chats = (session.query(Chats)
                 .filter(Chats.chat_id == new_id)
                 .all())
        while chats:
            new_id = str(random.randint(1000, 9999))
            chats = (session.query(Chats)
                     .filter(Chats.chat_id == new_id)
                     .all())

        new_chat = Chats(net_id1=user,
                         net_id2=matchid,
                         chat_id=new_id)

        session.add(new_chat)
        session.commit()

        session.close()
        engine.dispose()
        return id

    except Exception as ex:
        session.close()
        engine.dispose()
        print(ex, file=stderr)
        print("Data base connection failed", file=stderr)
        return "unknown (database connection failed)"


# Takes chat_id, message content, and sender (net_id), and adds to
# database
def send_chat(chat_id, sender, message):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        now = str(datetime.now(timezone('US/Eastern')))

        new_message = Messages(chat_id=chat_id,
                               sender_id=sender,
                               message_content=message,
                               date_time=now,
                               is_read=False)

        session.add(new_message)

        # update latest timestamp
        chat = (session.query(Chats).filter(Chats.chat_id == chat_id).first())
        chat.latest_date_time = now

        session.commit()
        session.close()
        engine.dispose()

    except Exception as ex:
        session.close()
        engine.dispose()
        print(ex, file=stderr)
        print("Data base connection failed", file=stderr)
        return "unknown (database connection failed)"


# get all message history from a given chat_id
# UPDATE: marks messages as read depending on user (net_id) seeing messages
def get_messages(chat_id, user):
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
            if user != sender:
                msg.is_read = True
            sender = get_user_bio(sender)[0]
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


# returns the most recent message in a given chat
def get_most_recent_message(chat_id):
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        chat = (session.query(Messages)
                .filter(Messages.chat_id == chat_id)
                .order_by(desc(Messages.date_time))
                .first())

        session.close()
        engine.dispose()

        if chat is not None:
            user = get_user_bio(chat.sender_id)[0]
            chat = (user, str(chat.message_content), str(chat.date_time))
        return chat

    except Exception as ex:
        session.close()
        engine.dispose()
        print(ex, file=stderr)
        print("Data base connection failed", file=stderr)
        return "unknown (database connection failed)"


# returns true or false if a user (net_id) has unread messages in a given chat
def is_unread(chat_id, user):
    engine = create_engine(DATABASE_URL)

    Session = sessionmaker(bind=engine)
    session = Session()

    chat = (session.query(Messages)
            .filter(Messages.chat_id == chat_id)
            .filter(Messages.sender_id != user)
            .filter(Messages.is_read == 'false')
            .first())

    session.close()
    engine.dispose()

    if chat is None:
        return False
    return True


# returns true or false if a chat has no messages
def is_empty(chat_id):
    engine = create_engine(DATABASE_URL)

    Session = sessionmaker(bind=engine)
    session = Session()

    chat = (session.query(Messages)
            .filter(Messages.chat_id == chat_id)
            .first())

    session.close()
    engine.dispose()

    if chat is None:
        return True
    return False


# unit test
def main():
    print("USER'S CHAT TESTS:")
    myself = 'collado'
    chats = get_all_chats(myself)
    print(chats)
    id1 = get_chat_id(myself, 'haha371')
    print(id1)
    id2 = get_chat_id(myself, 'Kenny')
    print(id2)
    send_chat(id1, myself, 'hello person 1')
    send_chat(id2, myself, 'hello person 2')
    msgs1 = get_messages(id1, myself)
    print(msgs1)
    msgs2 = get_messages(id2, myself)
    print(msgs2)
    unread1 = is_unread(id1, myself)
    print("Chat 1 unread? " + str(unread1))
    unread2 = is_unread(id2, myself)
    print("Chat 2 unread? " + str(unread2))

    print("MOST RECENT MSG TESTS: ")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    chats = session.query(Chats).all()

    for chat in chats:
        msg = get_most_recent_message(chat.chat_id)
        if msg is not None:
            print(str(chat.chat_id) + ": " + str(msg[1]))
            chat.latest_date_time = msg[2]

    session.commit()
    session.close()
    engine.dispose()


# ----------------------------------------------------------------------


if __name__ == '__main__':
    main()
