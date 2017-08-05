from psycopg2cffi import compat
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tg_bot.models import Base, Notes, Permissions, UserInfo
from tg_bot.config import Development as Configuration
from tg_bot.modules.locks import lock_types

compat.register()

engine = create_engine(Configuration.SQLALCHEMY_DATABASE_URI)

Base.metadata.create_all(engine)

Session = sessionmaker(autoflush=False)
sess = Session(bind=engine)


# Note: chat_id's are stored as strings because the int is over 32 bits.
def add_note_to_db(chat_id, notename, note_data):
    prev = sess.query(Notes).get((str(chat_id), notename))
    if prev:
        prev.value = note_data
        note = prev
    else:
        note = Notes(str(chat_id), notename, note_data)
    sess.add(note)
    sess.commit()


def get_note(chat_id, notename):
    return sess.query(Notes).get((str(chat_id), notename))


def rm_note(chat_id, notename):
    note = sess.query(Notes).get((str(chat_id), notename))
    if note:
        sess.delete(note)
        sess.commit()


# New chat added -> setup permissions
def init_permissions(chat_id, force=False):
    curr_perms = sess.query(Permissions).filter(Permissions.chat_id == str(chat_id)).all()
    if len(lock_types) != len(curr_perms) or force:
        for elem in curr_perms:
            sess.delete(elem)
        sess.flush()
        for lock in lock_types:
            perm = Permissions(str(chat_id), lock)
            sess.add(perm)
        sess.commit()


def update_lock(chat_id, lock_type, locked):
    curr_perms = sess.query(Permissions).get((str(chat_id), lock_type))
    if not curr_perms:
        print("Perms didnt exist! creating")
        init_permissions(chat_id, force=True)
        curr_perms = sess.query(Permissions).get((str(chat_id), lock_type))
    curr_perms.locked = locked
    sess.add(curr_perms)  # NOTE do i really need to commit...?
    sess.commit()


# TODO: in memory keystore loaded at bot start
def is_locked(chat_id, lock_type):
    curr_perms = sess.query(Permissions).get((str(chat_id), lock_type))
    if not curr_perms:
        print("Perms didnt exist! creating")
        init_permissions(chat_id, force=True)
        curr_perms = sess.query(Permissions).get((str(chat_id), lock_type))
        sess.add(curr_perms)
        sess.commit()
    return curr_perms.locked


def get_user_info(user_id):
    userinfo = sess.query(UserInfo).get(user_id)
    if userinfo:
        return userinfo.info
    return None


def set_user_info(user_id, info):
    userinfo = sess.query(UserInfo).get(user_id)
    if userinfo:
        userinfo.info = info
    else:
        userinfo = UserInfo(user_id, info)
    sess.add(userinfo)
    sess.commit()
