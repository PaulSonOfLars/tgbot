from tg_bot.modules.sql import session
from tg_bot.models import Owing, Person


def get_owers():
    people = session.query(Owing).distinct(Owing.ower).all()
    return [person.ower for person in people]


def add_person(name):
    if session.query(Person).get(name) is None:
        person = Person(name)
        session.add(person)
        session.commit()
        return True
    return False  # Already exists


def get_owees(ower):
    owees = session.query(Owing).filter(Owing.ower == ower).all()
    return [person.owee for person in owees]


def get_sum(ower, owee):
    amount = session.query(Owing).filter(Owing.ower == ower, Owing.owee == owee).one().amount
    return amount


def set_sum(ower, owee, amount):
    owed = session.query(Owing).filter(Owing.ower == ower, Owing.owee == owee).first()
    if owed is None:
        owed = Owing(ower, owee, amount)
    else:
        owed.amount += amount
    session.add(owed)
    session.commit()
    return owed.ower + " owes " + owed.owee + " " + str(owed.amount)
