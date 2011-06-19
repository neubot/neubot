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

import getopt
import sqlite3
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.database import DatabaseManager
from neubot.database import table_speedtest

#
# Open the database through the database manager
# so we get gratis the bonus that the database is
# automatically migrated to the latest version,
# and we get all the algorithms and the tables we
# need.
#
def open_dbm(path):
    dbm = DatabaseManager()
    dbm.set_path(path)
    dbm.connect()
    dbm.dbc.row_factory = sqlite3.Row   #XXX
    return dbm

#
# Wrapper for the output database.
#
# XXX We assume that there is at least one second between
# one database and the next one, unless they are overlapped,
# in which case we should discard the leading tuples that
# overlap.
#
class OutputWrapper(object):
    def __init__(self, path):
        self.dbm = open_dbm(path)
        self.since = 0

    def insert(self, row):
        dictionary = dict(row)
        table_speedtest.insert(self.dbm.connection(), dictionary,
          commit=False, override_timestamp=False)
        self.since = int(dictionary["timestamp"])

    def commit(self):
        self.dbm.dbc.commit()

USAGE = "Usage: tool_collate.py [--sparse] [-o output] file [file...]\n"

#
# Collate a certain numbers of Neubot databases into the same
# output database.  Note that it's possible to pass this script
# also overlapping databases: the code prunes the overlapping
# part of each database and executes VACUUM to reclaim for free
# space, unless --sparse is specified via command line.
#
def main(args):
    try:
        options, arguments = getopt.getopt(args[1:], "o:", ["sparse"])
    except getopt.error:
        sys.stderr.write(USAGE)
        sys.exit(1)

    outfile = "__database__.sqlite3"
    sparse = False

    for key, value in options:
        if key == "-f":
            outfile = value
        elif key == "--sparse":
            sparse = True

    if not arguments:
        sys.stdout.write(USAGE)
        sys.exit(0)

    output_wrapper = OutputWrapper(outfile)
    sys.stderr.write("* Output database file: %s\n" % outfile)

    for path in arguments:
        input_dbm = open_dbm(path)
        if not sparse:
            #
            # When some parts of the database overlap remove the
            # overlapping part and make sure the database does not
            # wast disk space with garbage.
            # CAVEAT You must use --sparse if you collate databases
            # coming from different test servers!
            #
            sys.stderr.write("* Removing overlapping parts: %s... " % path)
            table_speedtest.prune(input_dbm.connection(), output_wrapper.since)
            input_dbm.connection().execute("VACUUM;")
            sys.stderr.write("done\n")
        sys.stderr.write("* Processing rows in file: %s... " %  path)
        table_speedtest.walk(input_dbm.connection(), output_wrapper.insert)
        sys.stderr.write("done\n")

    sys.stderr.write("* Committing changes to: %s\n" % outfile)
    output_wrapper.commit()

if __name__ == "__main__":
    main(sys.argv)
