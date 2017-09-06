from sqlalchemy import Column, Integer, ForeignKey, UnicodeText
from sqlalchemy.exc import IntegrityError

from tg_bot.modules.sql import SESSION, BASE


class Person(BASE):
    __tablename__ = "person"
    name = Column(UnicodeText, primary_key=True, unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Person {}>".format(self.name)


# TODO: use chat_ids too
class Owing(BASE):
    __tablename__ = "owing"
    owing_id = Column(Integer, primary_key=True)
    ower = Column(UnicodeText,
                  ForeignKey("person.name",
                             onupdate="CASCADE",
                             ondelete="CASCADE"),
                  nullable=False)
    owee = Column(UnicodeText,
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

Owing.__table__.create(checkfirst=True)
Person.__table__.create(checkfirst=True)


def get_owers():
    people = SESSION.query(Owing).distinct(Owing.ower).all()
    return [person.ower for person in people]


def add_person(name):
    if SESSION.query(Person).get(name) is None:
        person = Person(name)
        SESSION.add(person)
        try:
            SESSION.commit()
        except IntegrityError:
            SESSION.rollback()
        return True
    return False  # Already exists


def get_owees(ower):
    owees = SESSION.query(Owing).filter(Owing.ower == ower).all()
    return [person.owee for person in owees]


def get_sum(ower, owee):
    amount = SESSION.query(Owing).filter(Owing.ower == ower, Owing.owee == owee).one().amount
    return amount


def set_sum(ower, owee, amount):
    owed = SESSION.query(Owing).filter(Owing.ower == ower, Owing.owee == owee).first()
    if owed is None:
        owed = Owing(ower, owee, amount)
    else:
        owed.amount += amount
    SESSION.add(owed)
    try:
        SESSION.commit()
    except IntegrityError:
        SESSION.rollback()
    return owed.ower + " owes " + owed.owee + " " + str(owed.amount)
