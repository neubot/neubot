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

def main(args):
    arguments = args[1:]

    if len(arguments) != 1:
        sys.stderr.write("Usage: tool_users.py file\n")
        sys.exit(1)

    connection = sqlite3.connect(arguments[0])

    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(DISTINCT(uuid)) FROM speedtest;")
    sys.stdout.write("%s: %d\n" % (arguments[0], cursor.next()[0]))

if __name__ == "__main__":
    main(sys.argv)
