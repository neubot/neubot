# neubot/database/_table_utils.py

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

#
# Set of functions that you can use to build queries
# for your tables given a template passed as input.
# The template is the python dict() representation of
# a table row and must only contain scalar primitive
# types, i.e. integer, string and float.
#

import types

#
# This is the generic mechanism that allows the plugin
# programmer to skip the step of writing down queries at
# hand.  Queries are created automatically given the
# table name and a template dictionary.
#
SIMPLE_TYPES = {
    types.StringType  : "TEXT NOT NULL",
    types.UnicodeType : "TEXT NOT NULL",
    types.IntType     : "INTEGER NOT NULL",
    types.FloatType   : "REAL NOT NULL",
}

def verify_template(template):
    for items in template:
        if type(items[1]) not in SIMPLE_TYPES:
            raise RuntimeError("Invalid template")

#
# Given the table name and a dictionary as a template this
# function returns the query to create a table with the given
# name suitable for holdings data from such dictionary.
#
def make_create_table(table, template):
    vector = [ "CREATE TABLE IF NOT EXISTS %s (" % table ]
    vector.append("id INTEGER PRIMARY KEY")
    vector.append(", ")

    for key, value in template.items():
        value = SIMPLE_TYPES[type(value)]
        vector.append("%s %s" % (key, value))
        vector.append(", ")

    vector[-1] = ");"
    query = "".join(vector)
    return query

#
# Given the table name and a template dictionary this function
# returns the query to insert something like that dictionary into
# the given table.
#
def make_insert_into(table, template):
    vector = [ "INSERT INTO %s VALUES (" % table ]
    vector.append("NULL")
    vector.append(", ")

    for items in template.items():
        vector.append(":%s" % items[0])
        vector.append(", ")

    vector[-1] = ");"
    query = "".join(vector)
    return query

#
# Given the table name, a template dictionary and a set
# of zero or more keyword arguments, this function builds
# a query to walk the specified table.
# XXX This function assumes that each table has a field
# which is named timestamp, with obvious semantic.
#
def make_select(table, template, **kwargs):
    vector = [ "SELECT " ]

    for items in template.items():
        vector.append("%s" % items[0])
        vector.append(", ")

    vector[-1] = " FROM %s" % table

    since, until = -1, -1
    if "since" in kwargs:
        since = int(kwargs["since"])
    if "until" in kwargs:
        until = int(kwargs["until"])

    if since >= 0 or until >= 0:
        vector.append(" WHERE ")
        if since >= 0:
            vector.append("timestamp >= :since")
        if since >= 0 and until >= 0:
            vector.append(" AND ")
        if until >= 0:
            vector.append("timestamp < :until")

    vector.append(" ORDER BY timestamp DESC")
    vector.append(";")
    query = "".join(vector)
    return query
