import threading

from sqlalchemy import Column, Integer, UnicodeText, String, ForeignKey, UniqueConstraint, func

from tg_bot import dispatcher
from tg_bot.modules.sql import BASE, SESSION


class Users(BASE):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    username = Column(UnicodeText)

    def __init__(self, user_id, username=None):
        self.user_id = user_id
        self.username = username

    def __repr__(self):
        return "<User {} ({})>".format(self.username, self.user_id)


class Chats(BASE):
    __tablename__ = "chats"
    chat_id = Column(String(14), primary_key=True)
    chat_name = Column(UnicodeText, nullable=False)

    def __init__(self, chat_id, chat_name):
        self.chat_id = chat_id
        self.chat_name = chat_name

    def __repr__(self):
        return "<Chat {} ({})>".format(self.chat_name, self.chat_id)


class ChatMembers(BASE):
    __tablename__ = "chat_members"
    priv_chat_id = Column(Integer, primary_key=True)
    # NOTE: Use dual primary key instead of private primary key?
    chat = Column(String(14),
                  ForeignKey("chats.chat_id",
                             onupdate="CASCADE",
                             ondelete="CASCADE"),
                  nullable=False)
    user = Column(Integer,
                  ForeignKey("users.user_id",
                             onupdate="CASCADE",
                             ondelete="CASCADE"),
                  nullable=False)
    __table_args__ = (UniqueConstraint('chat', 'user', name='_chat_members_uc'),)

    def __init__(self, chat, user):
        self.chat = chat
        self.user = user

    def __repr__(self):
        return "<Chat user {} ({}) in chat {} ({})>".format(self.user.username, self.user.user_id,
                                                            self.chat.chat_name, self.chat.chat_id)


Users.__table__.create(checkfirst=True)
Chats.__table__.create(checkfirst=True)
ChatMembers.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.Lock()


def ensure_bot_in_db():
    with INSERTION_LOCK:
        bot = Users(dispatcher.bot.id, dispatcher.bot.username)
        SESSION.merge(bot)
        SESSION.commit()


def update_user(user_id, username, chat_id, chat_name):
    with INSERTION_LOCK:
        user = SESSION.query(Users).get(user_id)
        if not user:
            user = Users(user_id, username)
            SESSION.add(user)
            SESSION.flush()
        else:
            user.username = username

        chat = SESSION.query(Chats).get(str(chat_id))
        if not chat:
            chat = Chats(str(chat_id), chat_name)
            SESSION.add(chat)
            SESSION.flush()

        else:
            chat.chat_name = chat_name

        member = SESSION.query(ChatMembers).filter(ChatMembers.chat == chat.chat_id,
                                                   ChatMembers.user == user.user_id).first()
        if not member:
            chat_member = ChatMembers(chat.chat_id, user.user_id)
            SESSION.add(chat_member)

        SESSION.commit()


def get_user_by_name(username):
    return SESSION.query(Users).filter(func.lower(Users.username) == username.lower()).first()


def get_chat_members(chat_id):
    return SESSION.query(ChatMembers).filter(ChatMembers.chat == str(chat_id)).all()


def get_all_chats():
    return SESSION.query(Chats).all()


# TODO: migrate chat_members too
def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = SESSION.query(Chats).get(str(old_chat_id))
        if chat:
            chat.chat_id = new_chat_id
            SESSION.add(chat)

        SESSION.commit()


ensure_bot_in_db()
