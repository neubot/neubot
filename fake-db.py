#!/usr/bin/env python

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
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
# Create fake database for testing
#

from subprocess import call
from sqlite3 import connect
from sys import stderr
from sys import argv

if __name__ == "__main__":
    if len(argv) != 2:
        stderr.write("Usage: %s database\n" % argv[0])
        exit(1)
    call(["/usr/bin/env", "python", "neubot/database.py", "-i", argv[1]])
    connection = connect(argv[1])
    cursor = connection.cursor()
    count = 0
    while count < 16384:
        cursor.execute('insert into results values(null,"x","x",1,"x");')
        count = count + 1
    connection.commit()
    cursor.close()
    connection.close()
