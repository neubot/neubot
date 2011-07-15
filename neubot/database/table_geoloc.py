# neubot/database/table_geoloc.py

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

def create(connection, commit=True):
    connection.execute("""CREATE TABLE IF NOT EXISTS geoloc(
      id INTEGER PRIMARY KEY, country TEXT, address TEXT);""")
    if commit:
        connection.commit()

def insert_server(connection, country, address, commit=True):
    connection.execute("""INSERT INTO geoloc VALUES (
      null, ?, ?);""", (country, address))
    if commit:
        connection.commit()

def lookup_servers(connection, country):
    cursor = connection.cursor()
    cursor.execute("SELECT address FROM geoloc WHERE country=?;", (country,))
    vector = map(lambda result: result[0], cursor)
    cursor.close()
    return vector
