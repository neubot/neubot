# neubot/arcfour.py

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

import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.times import timestamp
from neubot.utils import speed_formatter
from neubot.times import ticks

from neubot.log import LOG


class PassThrough(object):
    def __init__(self, key):
        LOG.debug("arcfour: ARC4 support not available")
        self.key = key

    def encrypt(self, data):
        return data

    def decrypt(self, data):
        return data


try:
    from Crypto.Cipher import ARC4
    ARCFOUR = ARC4.new
except ImportError:
    ARCFOUR = PassThrough

def arcfour_new(key=None):
    if not key:
        key = "neubot"
    return ARCFOUR(key)


class RandomData(object):

    """Ugly class that at the same time implements chunked
       transfer encoding and obfuscation."""

    def __init__(self, poller, t, chunkify=False):
        self.done = False
        self.chunkify = chunkify
        self.eof = False

        key = str(ticks())
        encoder = arcfour_new(key)
        self.encode = encoder.encrypt

        poller.sched(float(t), self.end_of_file)

    def end_of_file(self):
        self.eof = True

    def read(self, n):
        vector = []

        if self.done:
            pass

        elif self.eof:
            if self.chunkify:
                vector.append("0\r\n")
                vector.append("\r\n")
            self.done = True

        else:
            if self.chunkify:
                vector.append("%x\r\n" % n)

            data = "A" * n
            data = self.encode(data)
            vector.append(data)

            if self.chunkify:
                vector.append("\r\n")

        return "".join(vector)


if __name__ == "__main__":
    begin = ticks()
    m = "A" * 32768
    arc4 = arcfour_new()
    count = 0

    try:
        while True:
            e = arc4.encrypt(m)
            count += len(m)
    except KeyboardInterrupt:
        sys.stdout.write("\n")

    end = ticks()
    speed = count / (end - begin)
    speed = speed_formatter(speed)

    sys.stdout.write(speed)
    sys.stdout.write("\n")
