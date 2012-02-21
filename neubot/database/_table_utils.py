# neubot/database/_table_utils.py

#
# Copyright (c) 2011-2012 Simone Basso <bassosimone@gmail.com>,
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

'''
 Set of functions that you can use to build queries
 for your tables given a template passed as input.
 The template is the python dict() representation of
 a table row and must only contain scalar primitive
 types, i.e. integer, string and float.
'''

import re
import types

from neubot.simplejson.ordered_dict import OrderedDict

from neubot import utils

#
# This is the generic mechanism that allows the plugin
# programmer to skip the step of writing down queries at
# hand.  Queries are created automatically given the
# table name and a template dictionary.
#
SIMPLE_TYPES = {
    types.StringType  : "TEXT",
    types.UnicodeType : "TEXT",
    types.IntType     : "INTEGER",
    types.FloatType   : "REAL",
}

def __check(value):

    '''
     Make sure that we receive valid field names and values
     only when building the query.
    '''

    # A simple type?
    if type(value) not in SIMPLE_TYPES:
        raise ValueError("Not a simple type")

    # Not a string?
    if type(value) not in (types.StringType, types.UnicodeType):
        return value

    # Is the string valid?
    stripped = re.sub(r"[^A-Za-z0-9_]", "", value)
    if stripped != value:
        raise ValueError("Invalid string")

    return value

def make_create_table(table, template):

    '''
     Given the table name and a dictionary as a template this
     function returns the query to create a table with the given
     name suitable for holdings data from such dictionary.
    '''

    vector = [ "CREATE TABLE IF NOT EXISTS %s (" % __check(table) ]
    vector.append("id INTEGER PRIMARY KEY")
    vector.append(", ")

    for key, value in template.items():
        key = __check(key)
        value = SIMPLE_TYPES[type(__check(value))]
        vector.append("%s %s" % (key, value))
        vector.append(", ")

    vector[-1] = ");"
    query = "".join(vector)
    return query

def make_insert_into(table, template):

    '''
     Given the table name and a template dictionary this function
     returns the query to insert something like that dictionary into
     the given table.
    '''

    vector = [ "INSERT INTO %s (" % __check(table) ]
    vector.append("id")
    vector.append(", ")

    #
    # We MUST prepare this way the query because some tables
    # have been created at hand in the past and we cannot
    # guarantee that the order in which items are returned
    # by items() is the same that was used at hand.
    #
    for items in template.items():
        vector.append("%s" % __check(items[0]))
        vector.append(", ")

    vector[-1] = ") "

    vector.append("VALUES (NULL")
    vector.append(", ")

    for items in template.items():
        vector.append(":%s" % __check(items[0]))
        vector.append(", ")

    vector[-1] = ");"
    query = "".join(vector)
    return query

def do_insert_into(connection, query, dictobj, template,
      commit=True, override_timestamp=True):

    '''
     Wrapper for INSERT INTO that makes sure that @dictobj
     has the same fields of @template, to avoid a programming
     error in sqlite3.  If @override timestamp is True, the
     function will also override @dictobj timestamp.  If
     @commit is True, the function will also commit to
     @database.
    '''

    for key in template.keys():
        if not key in dictobj:
            dictobj[key] = None

    # Override timestamp on server-side to guarantee consistency
    if override_timestamp:
        dictobj['timestamp'] = utils.timestamp()

    connection.execute(query, dictobj)

    if commit:
        connection.commit()

def make_select(table, template, **kwargs):

    '''
     Given the table name, a template dictionary and a set
     of zero or more keyword arguments, this function builds
     a query to walk the specified table.
    '''

    if not "timestamp" in template:
        raise ValueError("Template does not contain 'timestamp'")

    vector = [ "SELECT " ]

    for items in template.items():
        vector.append("%s" % __check(items[0]))
        vector.append(", ")

    vector[-1] = " FROM %s" % __check(table)

    since, until = -1, -1
    if "since" in kwargs:
        since = int(__check(kwargs["since"]))
    if "until" in kwargs:
        until = int(__check(kwargs["until"]))

    if since >= 0 or until >= 0:
        vector.append(" WHERE ")
        if since >= 0:
            vector.append("timestamp >= :since")
        if since >= 0 and until >= 0:
            vector.append(" AND ")
        if until >= 0:
            vector.append("timestamp < :until")

    if "desc" in kwargs and kwargs["desc"]:
        vector.append(" ORDER BY timestamp DESC")
    vector.append(";")
    query = "".join(vector)
    return query

def rename_column_query(table1, template1, table2, template2):

    ''' Returns the query that copies from table1, described by
        template1, to table2, described by template2 '''

    query = ["INSERT INTO %s(" % __check(table2)]
    for name in template2:
        query.append(__check(name))
        query.append(",")
    query[-1] = ") SELECT "
    for name in template1:
        query.append(__check(name))
        query.append(",")
    query[-1] = " FROM %s;" % __check(table1)

    query = "".join(query)
    return query

def rename_column_ntemplate(template, mapping, broken=False):

    ''' Creates new template for rename_column(), given the template
        and the changes mapping '''

    #
    # The problem with the broken algorithm is that there is
    # no guarantee that new template keys() are in same order
    # as template keys().  Hence, the column reordering bug
    # that hit migration from 4.1 to 4.2 schema.
    # Typically Neubot will use the nonbroken algorithm, but
    # the broken one is needed by migrate to try to fixup the
    # mess caused by the bug.
    #

    if not broken:
        ntemplate = OrderedDict()
    else:
        ntemplate = {}

    for key, value in template.items():
        if key in mapping:
            key = mapping[key]
        ntemplate[key] = value

    return ntemplate

def rename_column(connection, table, template, mapping, broken=False):

    ''' General procedure to rename one or more columns in a table,
        described by template, according to the specified mapping '''

    # See http://stackoverflow.com/questions/805363

    table = __check(table)
    otable = "old_%s" % table

    ntemplate = rename_column_ntemplate(template, mapping, broken)

    connection.execute("ALTER TABLE %s RENAME TO %s" % (table, otable))
    connection.execute(make_create_table(table, ntemplate))
    connection.execute(rename_column_query(otable, template, table, ntemplate))
    connection.execute("DROP TABLE %s;" % otable)
