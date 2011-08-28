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
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.database import table_speedtest

MAX_DOWNLOAD_SPEED = (20 * 1000 * 1000)/8.0
MAX_LATENCY = 0.1

#
# Select only rows with a download speed lower than 20
# Mbit/s and a "latency" lower than 100 ms.  The idea here
# is to consider only users that were reasonably near our
# server (in terms of bandwidth-delay product).
#
def main(args):
    arguments = args[1:]

    if len(arguments) != 1:
        sys.stderr.write("Usage: tool_goodset.py file\n")
        sys.exit(1)

    # Because I'm lazy below
    if not arguments[0].endswith(".sqlite3"):
        sys.stderr.write("error: Input file must end with .sqlite3\n")
        sys.exit(1)

    outfile = arguments[0].replace(".sqlite3", "-goodset.sqlite3")
    sys.stderr.write("* Output database file: %s\n" % outfile)
    output = sqlite3.connect(outfile)
    table_speedtest.create(output)

    sys.stderr.write("* Processing file: %s... " %  arguments[0])
    input_dbm = sqlite3.connect(arguments[0])
    input_dbm.row_factory = sqlite3.Row

    # Get the number of rows in the original database
    cursor = input_dbm.cursor()
    cursor.execute("SELECT COUNT(*) FROM speedtest;")
    total = cursor.next()[0]

    # Copy the goodset to the new database
    cursor = input_dbm.cursor()
    cursor.execute("""SELECT * FROM speedtest WHERE download_speed < ?
      AND latency < ?;""", (MAX_DOWNLOAD_SPEED, MAX_LATENCY))
    for row in cursor:
        table_speedtest.insert(output, dict(row), commit=False,
          override_timestamp=False)
    sys.stderr.write("done\n")

    sys.stderr.write("* Committing changes to: %s\n" % outfile)
    output.commit()

    # Get the number of rows in the new database
    cursor = output.cursor()
    cursor.execute("SELECT COUNT(*) FROM speedtest;")
    goodset = cursor.next()[0]

    if total:
        sys.stdout.write("%d/%d (%.2f%%)\n" % (goodset, total,
          goodset * 100.0 / total))
    else:
        sys.stdout.write("0/0 (0.00%)\n")

if __name__ == "__main__":
    main(sys.argv)
