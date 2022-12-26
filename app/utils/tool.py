import datetime
from rethinkdb import r


def time_now():
    return datetime.datetime.now(r.make_timezone("+08:00"))
