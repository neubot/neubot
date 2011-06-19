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

class Histo(object):
    def __init__(self, name, bucket, max, convert, unit):
        self.name = name
        self.bucket = bucket
        self.max = max
        self.convert = convert
        self.unit = unit

        self.overflow = 0
        self.vector = []
        self.done = False

        for t in range(int(self.max/self.bucket)):
           self.vector.append(0)

    def add_result(self, t):
        t = int(self.convert(t) / self.bucket)
        if t < 0:
            sys.stderr.write("Warning: passed negative value\n")
        elif t < len(self.vector):
            self.vector[t] += 1
        else:
            self.overflow += 1

    def _finished(self):
        if not self.done:
            self.done = True
            self.vector[-1] += self.overflow

    def write(self, template):
        self._finished()
        path = template.replace(".sqlite3", "-%s.txt" % self.name)
        fp = open(path, "wb")
        fp.write("# bucket: %(bucket)d, max: %(max)d, unit: %(unit)s\n"
                 % vars(self))
        for idx, value in enumerate(self.vector):
            fp.write("%d\t%d\n" % (idx, value))

LATENCY = Histo("latency", 20, 100, lambda t: 1000 * t, "ms")
DOWNLOAD = Histo("download", 1, 20, lambda s: (s * 8)/(1000 * 1000), "Mbit/s")
UPLOAD = Histo("upload", 100, 20000, lambda s: (s * 8)/(1000), "Kbit/s")

def main(args):
    arguments = args[1:]

    if len(arguments) != 1:
        sys.stderr.write("Usage: tool_users.py file\n")
        sys.exit(1)

    # Because I'm lazy below
    if not arguments[0].endswith(".sqlite3"):
        sys.stderr.write("error: Input file name must end with .sqlite3\n")
        sys.exit(1)

    connection = sqlite3.connect(arguments[0])
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM speedtest;")
    for row in cursor:
        LATENCY.add_result(row['latency'])
        DOWNLOAD.add_result(row['download_speed'])
        UPLOAD.add_result(row['upload_speed'])

    for v in (LATENCY, DOWNLOAD, UPLOAD):
        v.write(arguments[0])

if __name__ == "__main__":
    main(sys.argv)
