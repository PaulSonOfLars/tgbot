from sqlalchemy import Column, Text, String, Boolean, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Notes(Base):
    __tablename__ = "notes"
    chat_id = Column(String(14), primary_key=True)
    name = Column(Text, primary_key=True)
    value = Column(Text, nullable=False)

    def __init__(self, chat_id, name, value):
        self.chat_id = str(chat_id)  # ensure string
        self.name = name
        self.value = value

    def __repr__(self):
        return "<Note %s>" % self.name


# TODO: add gifs
class Permissions(Base):
    __tablename__ = "permissions"
    chat_id = Column(String(14), primary_key=True)
    audio = Column(Boolean)
    voice = Column(Boolean)
    contact = Column(Boolean)
    video = Column(Boolean)
    document = Column(Boolean)
    photo = Column(Boolean)
    sticker = Column(Boolean)

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


class UserInfo(Base):
    __tablename__ = "userinfo"
    user_id = Column(Integer, primary_key=True)
    info = Column(Text)

    def __init__(self, user_id, info):
        self.user_id = user_id
        self.info = info

    def __repr__(self):
        return "<User info %d>" % self.user_id


class Person(Base):
    __tablename__ = "person"
    name = Column(Text, primary_key=True, unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Person {}>".format(self.name)


class Owing(Base):
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
