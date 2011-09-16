#!/usr/bin/env python

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

import sqlite3
import unittest
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.database import table_config

class TestConfig(unittest.TestCase):

    def runTest(self):

        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row

        v, v2 = [], []
        table_config.create(connection)
        for name, value in table_config.dictionarize(connection).items():
            v.append((name, value))
        table_config.create(connection)
        for name, value in table_config.dictionarize(connection).items():
            v2.append((name, value))
        self.assertEquals(v, v2)

        table_config.update(connection, {"uuid": ""}.iteritems())
        result = table_config.dictionarize(connection)
        #
        # The version number changes as time passes and we don't
        # want to keep the test uptodate.
        #
        del result['version']
        self.assertEquals(result, {"uuid": ""})

        table_config.update(connection, {}.iteritems(), clear=True)
        self.assertEquals(table_config.dictionarize(connection), {})

        table_config.create(connection)
        print(table_config.jsonize(connection))

if __name__ == '__main__':
    unittest.main()
