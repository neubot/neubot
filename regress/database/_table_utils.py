#!/usr/bin/env python

#
# Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>,
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

''' Regression tests for neubot/database/_table_utils.py '''

import unittest
import sqlite3
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.database import _table_utils

class TestRenameColumn(unittest.TestCase):

    ''' Regression test for rename_column() feature '''

    template = {
                'namex': 'Simone',
                'sur_name': 'Basso',
                'age': 29,
               }

    mapping = {
               'namex': 'name',
               'sur_name': 'surname'
              }

    def test_success(self):
        ''' Test for the successful case '''
        connection = sqlite3.connect(':memory:')
        connection.execute(_table_utils.make_create_table(
                           'Person', self.template))
        _table_utils.rename_column(connection, 'Person', self.template,
                                   self.mapping)
        cursor = connection.cursor()
        cursor.execute('SELECT sql FROM sqlite_master WHERE name="Person";')
        query = cursor.next()[0]
        self.assertEqual(query, 'CREATE TABLE Person (id INTEGER PRIMARY '
                                'KEY, age INTEGER, surname TEXT, name TEXT)')

if __name__ == '__main__':
    unittest.main()
