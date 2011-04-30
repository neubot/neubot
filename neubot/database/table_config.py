# neubot/database/table_config.py

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

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

from neubot.utils import get_uuid
from neubot import compat

#
# Config table.
# The config table is like a dictionary and keeps some useful
# variables.  It keeps the version of the database format, that
# might be useful in the future to convert an old database to
# a new one, should we change the format.
#
# <on uuid and privacy>
# It also keeps an unique identifier for each neubot client
# which we believe would help data analysis, e.g. we could
# review the measurement history of a given neubot looking for
# certain patterns, such as the connection speed decreasing
# near the end of the month because the user exceeded a
# bandwidth cap.
#
# We believe this should have a negligible impact on privacy
# because it would, at most, allow to say that neubot XYZ owner
# changed IP address, and hence, possibly, provider and/or
# location (and note that this information is functional to
# our goal of building a network neutrality map organized by
# geographic location and provider).
#
# So, we believe you should not be concerned by this issue,
# but, in case you were, the way to go is `neubot database -f`
# that forces neubot to generate and use A NEW uuid.
# </on uuid and privacy>
#

def create(connection, commit=True):
    connection.execute("""CREATE TABLE IF NOT EXISTS config(
      name TEXT PRIMARY KEY, value TEXT);""")
    connection.execute("""INSERT OR IGNORE INTO config VALUES(
      'version', '2.0');""")
    connection.execute("""INSERT OR IGNORE INTO config VALUES(
      'uuid', ?);""", (get_uuid(),))
    if commit:
        connection.commit()

def update(connection, iterator, commit=True, clear=False):
    if clear:
        connection.execute("DELETE FROM config;")
    connection.executemany("""INSERT OR REPLACE INTO config VALUES(
      ?,?);""", iterator)
    if commit:
        connection.commit()

def walk(connection, func):
    cursor = connection.cursor()
    cursor.execute("SELECT name, value FROM CONFIG;")
    return map(func, cursor)

def dictionarize(connection):
    d = {}
    walk(connection, lambda t: d.update([t]))
    return d

def jsonize(connection):
    return compat.json.dumps(dictionarize(connection))

if __name__ == "__main__":
    import sqlite3
    connection = sqlite3.connect(":memory:")

    v, v2 = [], []
    create(connection)
    walk(connection, v.append)
    create(connection)
    walk(connection, v2.append)
    if v != v2:
        raise RuntimeError

    update(connection, {"uuid": ""}.iteritems())
    if dictionarize(connection) != {"version": "2.0", "uuid": ""}:
        raise RuntimeError

    update(connection, {}.iteritems(), clear=True)
    if dictionarize(connection) != {}:
        raise RuntimeError

    create(connection)
    print jsonize(connection)
