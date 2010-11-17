# neubot/bittorrent/wrapper.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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
# Wrapper for BitTorrent protocol
#

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from connector import BTConnector
from neubot.net.listeners import listen
from neubot.net.connectors import connect
from handler import StreamWrapper
from neubot import log

class Upload:
    def __init__(self):
        pass

    def got_request(self, index, begin, length):
        pass

class Download:
    def __init__(self):
        pass

    def got_piece(self, index, begin, length):
        pass

class BitTorrent:
    def __init__(self):
        self.config = {}
        self.config["max_message_length"] = 1<<20
        self.infohash = "".join( ['\xaa']*20 )
        self.my_id = "".join( ['\xaa']*20 )

    def connection_handshake_completed(self, connector):
        connector.download = Download()
        connector.upload = Upload()
        connector.close() #XXX testing time...

    def connection_lost(self, connector):
        pass

    def make_connection(self, address, port):
        connect(address, port, self._connection_made)

    def _connection_made(self, stream):
        connection = StreamWrapper(stream)
        BTConnector(self, connection, self.my_id, True)

    def open_port(self, address, port):
        listen(address, port, self._incoming_connection)

    def _incoming_connection(self, stream):
        connection = StreamWrapper(stream)
        BTConnector(self, connection, self.my_id, False)

from sys import exit
from getopt import GetoptError
from neubot.net.pollers import loop
from sys import stdout, stderr
from getopt import getopt
from neubot import version
from sys import argv

USAGE =									\
"Usage: @PROGNAME@ -V\n"						\
"       @PROGNAME@ --help\n"						\
"       @PROGNAME@ -S [-v]\n"						\
"       @PROGNAME@ [-v]\n"

HELP = USAGE +                                                          \
"Options:\n"                                                            \
"  --help        : Print this help screen and exit.\n"                  \
"  -S            : Run the program in server mode.\n"                   \
"  -V            : Print version number and exit.\n"                    \
"  -v            : Run the program in verbose mode.\n"

def main(args):
    servermode = False
    # parse
    try:
        options, arguments = getopt(args[1:], "SVv", ["help"])
    except GetoptError:
        stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        exit(1)
    # options
    for name, value in options:
        if name == "--help":
            stdout.write(HELP.replace("@PROGNAME@", args[0]))
            exit(1)
        elif name == "-S":
            servermode = True
        elif name == "-V":
            stdout.write(version + "\n")
            exit(0)
        elif name == "-v":
            log.verbose()
    # run
    bittorrent = BitTorrent()
    if servermode:
        bittorrent.open_port("127.0.0.1", "6881")
        loop()
        exit(0)
    bittorrent.make_connection("127.0.0.1", "6881")
    loop()

if __name__ == "__main__":
    main(argv)
