from tg_bot.modules.sql import SESSION
from tg_bot.models import Owing, Person


def get_owers():
    people = SESSION.query(Owing).distinct(Owing.ower).all()
    return [person.ower for person in people]


def add_person(name):
    if SESSION.query(Person).get(name) is None:
        person = Person(name)
        SESSION.add(person)
        SESSION.commit()
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
    SESSION.commit()
    return owed.ower + " owes " + owed.owee + " " + str(owed.amount)
