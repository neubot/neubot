# neubot/database/table_log.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
#

from neubot.database import _table_utils
from neubot import utils

TEMPLATE = {
    "timestamp": 0,
    "severity": "",
    "message": "",
}

CREATE_TABLE = _table_utils.make_create_table("log", TEMPLATE)
INSERT_INTO = _table_utils.make_insert_into("log", TEMPLATE)

def create(connection, commit=True):
    connection.execute(CREATE_TABLE)
    if commit:
        connection.commit()

def insert(connection, dictobj, commit=True):
    connection.execute(INSERT_INTO, dictobj)
    if commit:
        connection.commit()

def walk(connection, func, since=-1, until=-1):
    cursor = connection.cursor()
    SELECT = _table_utils.make_select("log", TEMPLATE,
                            since=since, until=until)
    cursor.execute(SELECT, {"since": since, "until": until})
    return map(func, cursor)

def listify(connection, since=-1, until=-1):
    return walk(connection, lambda t: dict(t), since, until)

# Delete logs older than 30 days.
def prune(connection, days_ago=None, commit=True):
    if not days_ago:
        days_ago = 30
    until = utils.timestamp() - days_ago * 24 * 60 * 60
    connection.execute("DELETE FROM log WHERE timestamp < ?;", (until,))
    if commit:
        connection.commit()
