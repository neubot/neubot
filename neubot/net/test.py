# neubot/net/test.py

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
# Unit testing for neubot/net/streams.py (here because it could not
# stay at the end of such file because of circular dependencies)
#

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

class Discard:
    def __init__(self, stream):
        stream.recv(8000, self.got_data)

    def got_data(self, stream, octets):
        stream.recv(8000, self.got_data)

    def __del__(self):
        pass

class Echo:
    def __init__(self, stream):
        stream.recv(8000, self.got_data)

    def got_data(self, stream, octets):
        stream.send(octets, self.sent_data)

    def sent_data(self, stream, octets):
        stream.recv(8000, self.got_data)

    def __del__(self):
        pass

class Source:
    def __init__(self, stream):
        self.buffer = "A" * 8000
        stream.send(self.buffer, self.sent_data)

    def sent_data(self, stream, octets):
        stream.send(self.buffer, self.sent_data)

    def __del__(self):
        pass

from sys import argv
from sys import stdout
from sys import stderr
from sys import exit

from neubot.net.listeners import listen
from neubot.net.connectors import connect
from neubot.net.pollers import loop

if __name__ == "__main__":
    if len(argv) != 2:
        stdout.write("Usage: %s discard|echo|source\n" % argv[0])
        exit(1)
    elif argv[1] == "discard":
        listen("127.0.0.1", "8009", accepted=Discard)
        loop()
        exit(0)
    elif argv[1] == "echo":
        listen("127.0.0.1", "8007", accepted=Echo)
        loop()
        exit(0)
    elif argv[1] == "source":
        connect("127.0.0.1", "8009", connected=Source)
        loop()
        exit(0)
    else:
        stderr.write("Usage: %s discard|echo|source\n" % argv[0])
        exit(1)
