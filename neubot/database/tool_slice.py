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

import collections
import datetime
import sqlite3
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.database import table_speedtest

TIMES = collections.deque()
for month in range(10, 13):
    TIMES.append(datetime.date(2010, month, 1))
for month in range(1, 8):
    TIMES.append(datetime.date(2011, month, 1))

def main(args):
    arguments = args[1:]

    if len(arguments) != 1:
        sys.stderr.write("Usage: tool_slice.py file\n")
        sys.exit(1)

    # Because below I'm lazy
    if not arguments[0].endswith(".sqlite3"):
        sys.stderr.write("error: Input file must end with .sqlite3 suffix\n")
        sys.exit(1)

    connection = sqlite3.connect(arguments[0])
    connection.row_factory = sqlite3.Row

    since = TIMES.popleft()
    while TIMES:
        until = TIMES.popleft()
        output = sqlite3.connect(arguments[0].replace(".sqlite3",
          "_%d-%02d.sqlite3" % (since.year, since.month)))
        table_speedtest.create(output)

        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM speedtest WHERE timestamp >= ?
          AND timestamp < ?;""", (since.strftime("%s"), until.strftime("%s")))

        for row in cursor:
            table_speedtest.insert(output, dict(row), commit=False,
              override_timestamp=False)

        output.commit()
        since = until

if __name__ == "__main__":
    main(sys.argv)
