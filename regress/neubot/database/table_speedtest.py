#!/usr/bin/env python

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
# Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>,
#  Universita` degli Studi di Milano
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

import pprint
import sqlite3
import sys
import unittest

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.database import table_speedtest
from neubot import utils

from regress.neubot.database.table_speedtest_gen import ResultIterator

class TestDatabase(unittest.TestCase):

    def runTest(self):
        """Make sure speedtest table works as expected"""

        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        table_speedtest.create(connection)
        table_speedtest.create(connection)

        v = map(None, ResultIterator())
        for d in v:
            table_speedtest.insert(connection, d, override_timestamp=False)

        v1 = table_speedtest.listify(connection)
        self.assertEquals(sorted(v), sorted(v1))

        since = utils.timestamp() - 7 * 24 * 60 * 60
        until = utils.timestamp() - 3 * 24 * 60 * 60
        v2 = table_speedtest.listify(connection, since=since, until=until)
        self.assertTrue(len(v2) < len(v))

        table_speedtest.prune(connection, until)
        self.assertTrue(len(table_speedtest.listify(connection)) < len(v1))

if __name__ == "__main__":
    unittest.main()
