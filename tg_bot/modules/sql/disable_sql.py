import threading

from sqlalchemy import Column, String, UnicodeText, func, distinct

from tg_bot.modules.sql import SESSION, BASE


class Disable(BASE):
    __tablename__ = "disabled_commands"
    chat_id = Column(String(14), primary_key=True)
    command = Column(UnicodeText, primary_key=True)

    def __init__(self, chat_id, command):
        self.chat_id = chat_id
        self.command = command

    def __repr__(self):
        return "Disabled cmd {} in {}".format(self.command, self.chat_id)


Disable.__table__.create(checkfirst=True)
DISABLE_INSERTION_LOCK = threading.RLock()


def disable_command(chat_id, disable):
    with DISABLE_INSERTION_LOCK:
        disabled = SESSION.query(Disable).get((str(chat_id), disable))

        if not disabled:
            disabled = Disable(str(chat_id), disable)
            SESSION.add(disabled)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def enable_command(chat_id, enable):
    with DISABLE_INSERTION_LOCK:
        disabled = SESSION.query(Disable).get((str(chat_id), enable))

        if disabled:
            SESSION.delete(disabled)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def is_command_disabled(chat_id, cmd):
    try:
        return bool(SESSION.query(Disable).get((str(chat_id), cmd)))
    finally:
        SESSION.close()


def are_commands_disabled(chat_id, cmds):
    try:
        return bool(SESSION.query(Disable).filter(Disable.chat_id == str(chat_id),
                                                  Disable.command.in_(v for v in cmds)).first())
    finally:
        SESSION.close()


def get_all_disabled(chat_id):
    try:
        return SESSION.query(Disable).filter(Disable.chat_id == str(chat_id)).all()
    finally:
        SESSION.close()


def num_chats():
    try:
        return SESSION.query(func.count(distinct(Disable.chat_id))).scalar()
    finally:
        SESSION.close()


def num_disabled():
    try:
        return SESSION.query(Disable).count()
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with DISABLE_INSERTION_LOCK:
        chats = SESSION.query(Disable).filter(Disable.chat_id == str(old_chat_id)).all()
        if chats:
            for chat in chats:
                chat.chat_id = str(new_chat_id)
                SESSION.add(chat)

        SESSION.commit()
