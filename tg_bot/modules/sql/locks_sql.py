# New chat added -> setup permissions
from tg_bot.models import Permissions
from tg_bot.modules.sql import session


def init_permissions(chat_id, force=False):
    from tg_bot.modules.locks import LOCK_TYPES
    curr_perms = session.query(Permissions).filter(Permissions.chat_id == str(chat_id)).all()
    if len(LOCK_TYPES) != len(curr_perms) or force:
        for elem in curr_perms:
            session.delete(elem)
        session.flush()
        for lock in LOCK_TYPES:
            perm = Permissions(str(chat_id), lock)
            session.add(perm)
        session.commit()


def update_lock(chat_id, lock_type, locked):
    curr_perms = session.query(Permissions).get((str(chat_id), lock_type))
    if not curr_perms:
        print("Perms didnt exist! creating")
        init_permissions(chat_id, force=True)
        curr_perms = session.query(Permissions).get((str(chat_id), lock_type))
    curr_perms.locked = locked
    session.add(curr_perms)  # NOTE do i really need to commit...?
    session.commit()


# TODO: in memory keystore loaded at bot start
def is_locked(chat_id, lock_type):
    curr_perms = session.query(Permissions).get((str(chat_id), lock_type))
    if not curr_perms:
        print("Perms didnt exist! creating")
        init_permissions(chat_id, force=True)
        curr_perms = session.query(Permissions).get((str(chat_id), lock_type))
        session.add(curr_perms)
        session.commit()
    return curr_perms.locked
