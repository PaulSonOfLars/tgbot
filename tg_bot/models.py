from sqlalchemy import Column, Text, String, Boolean, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

BASE = declarative_base()


class Notes(BASE):
    __tablename__ = "notes"
    chat_id = Column(String(14), primary_key=True)
    name = Column(Text, primary_key=True)
    value = Column(Text, nullable=False)
    is_reply = Column(Boolean, default=False)

    def __init__(self, chat_id, name, value, is_reply=False):
        self.chat_id = str(chat_id)  # ensure string
        self.name = name
        self.value = value
        self.is_reply = is_reply

    def __repr__(self):
        return "<Note %s>" % self.name


# TODO: add gifs
class Permissions(BASE):
    __tablename__ = "permissions"
    chat_id = Column(String(14), primary_key=True)
    audio = Column(Boolean, default=False)
    voice = Column(Boolean, default=False)
    contact = Column(Boolean, default=False)
    video = Column(Boolean, default=False)
    document = Column(Boolean, default=False)
    photo = Column(Boolean, default=False)
    sticker = Column(Boolean, default=False)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string
        self.audio = False
        self.voice = False
        self.contact = False
        self.video = False
        self.document = False
        self.photo = False
        self.sticker = False

    def __repr__(self):
        return "<Permissions for %s>" % self.chat_id


class UserInfo(BASE):
    __tablename__ = "userinfo"
    user_id = Column(Integer, primary_key=True)
    info = Column(Text)

    def __init__(self, user_id, info):
        self.user_id = user_id
        self.info = info

    def __repr__(self):
        return "<User info %d>" % self.user_id


class UserBio(BASE):
    __tablename__ = "userbio"
    user_id = Column(Integer, primary_key=True)
    bio = Column(Text)

    def __init__(self, user_id, bio):
        self.user_id = user_id
        self.bio = bio

    def __repr__(self):
        return "<User info %d>" % self.user_id


class Person(BASE):
    __tablename__ = "person"
    name = Column(Text, primary_key=True, unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Person {}>".format(self.name)


# TODO: use chat_ids too
class Owing(BASE):
    __tablename__ = "owing"
    owing_id = Column(Integer, primary_key=True)
    ower = Column(Text,
                  ForeignKey("person.name",
                             onupdate="CASCADE",
                             ondelete="CASCADE"),
                  nullable=False)
    owee = Column(Text,
                  ForeignKey("person.name",
                             onupdate="CASCADE",
                             ondelete="CASCADE"),
                  nullable=False)
    amount = Column(Integer, nullable=False)

    def __init__(self, ower, owee, amount=0):
        self.ower = ower
        self.owee = owee
        self.amount = amount

    def __repr__(self):
        return "<{} owes {} {}>".format(self.ower, self.owee, self.amount)


class Welcome(BASE):
    __tablename__ = "welcome_pref"
    chat_id = Column(String(14), primary_key=True)
    should_welcome = Column(Boolean, default=True)

    def __init__(self, chat_id, should_welcome=True):
        self.chat_id = chat_id
        self.should_welcome = should_welcome

    def __repr__(self):
        return "<Chat {} should Welcome new users: {}>".format(self.chat_id, self.should_welcome)
