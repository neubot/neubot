# neubot/bittorrent/main.py

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
import getopt

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.bittorrent.streams import BTStream
from neubot.net.streams import Connector
from neubot.net.streams import Listener
from neubot.options import OptionParser
from neubot import log

from neubot.net.streams import verboser as VERBOSER
from neubot.net.streams import measurer as MEASURER
from neubot.net.pollers import poller as POLLER

from neubot.arcfour import arcfour_new

class Upload(object):

    """Responds to requests."""

    def __init__(self, handler):
        self.handler = handler
        self.scrambler = arcfour_new()

    def got_request(self, index, begin, length):
        data = "A" * length
        data = self.scrambler.encrypt(data)
        self.handler.send_piece(index, begin, data)

    def got_interested(self):
        pass

    def got_not_interested(self):
        pass

class Download(object):

    """Requests missing pieces."""

    def __init__(self, handler):
        self.handler = handler

    def got_piece(self, index, begin, length):
        self.handler.send_request(0, 0, 1<<15)

    def got_choke(self):
        pass

    def got_unchoke(self):
        pass

class BTConnectingPeer(Connector):

    """Connect to a given BitTorrent peer and controls the
       resulting connection."""

    def __init__(self, poller):
        Connector.__init__(self, poller)
        self.infohash = "".join( ['\xaa']*20 )
        self.my_id = "".join( ['\xaa']*20 )
        self.stream = BTStream

    def connection_failed(self, exception):
        VERBOSER.connection_failed(self.endpoint, exception, fatal=True)

    def started_connecting(self):
        VERBOSER.started_connecting(self.endpoint)

    def connection_made(self, handler):
        MEASURER.register_stream(handler)
        handler.initialize(self, self.my_id, True)
        handler.download = Download(handler)
        handler.upload = Upload(handler)

    def connection_handshake_completed(self, handler):
        handler.send_request(0, 0, 1<<15)

class BTListeningPeer(Listener):

    """Listens for connections from BitTorrent peers and controls the
       resulting connections."""

    def __init__(self, poller):
        Listener.__init__(self, poller)
        self.infohash = "".join( ['\xaa']*20 )
        self.my_id = "".join( ['\xaa']*20 )
        self.stream = BTStream

    def started_listening(self):
        VERBOSER.started_listening(self.endpoint)

    def accept_failed(self, exception):
        pass

    def bind_failed(self, exception):
        VERBOSER.connection_failed(self.endpoint, exception, fatal=True)

    def connection_made(self, handler):
        MEASURER.register_stream(handler)
        handler.initialize(self, self.my_id, True)
        handler.download = Download(handler)
        handler.upload = Upload(handler)

    def connection_handshake_completed(self, handler):
        pass

USAGE = """Neubot bittorrent -- Test unit for BitTorrent module

Usage: neubot bittorrent [-Vv] [-D macro[=value]] [-f file] [--help]

Options:
    -D macro[=value]   : Set the value of the macro `macro`
    -f file            : Read options from file `file`
    --help             : Print this help screen and exit
    -V                 : Print version number and exit
    -v                 : Run the program in verbose mode

Macros (defaults in square brackets):
    address=addr       : Select address to use               [127.0.0.1]
    listen             : Listen for incoming connections     [False]
    port=port          : Select the port to use              [6881]

"""

VERSION = "Neubot 0.3.5\n"

def main(args):

    conf = OptionParser()
    conf.set_option("bittorrent", "address", "127.0.0.1")
    conf.set_option("bittorrent", "listen", "False")
    conf.set_option("bittorrent", "port", "6881")

    try:
        options, arguments = getopt.getopt(args[1:], "D:f:Vv", ["help"])
    except getopt.GetoptError:
        sys.stderr.write(USAGE)
        sys.exit(1)

    if len(arguments) > 0:
        sys.stdout.write(USAGE)
        sys.exit(1)

    for name, value in options:
        if name == "-D":
             conf.register_opt(value, "bittorrent")
             continue
        if name == "-f":
             conf.register_file(value)
             continue
        if name == "--help":
             sys.stdout.write(USAGE)
             sys.exit(0)
        if name == "-V":
             sys.stdout.write(VERSION)
             sys.exit(0)
        if name == "-v":
             log.verbose()
             continue

    conf.merge_files()
    conf.merge_environ()
    conf.merge_opts()

    address = conf.get_option("bittorrent", "address")
    listen = conf.get_option_bool("bittorrent", "listen")
    port = conf.get_option_uint("bittorrent", "port")

    endpoint = (address, port)

    MEASURER.start()

    if listen:
        listener = BTListeningPeer(POLLER)
        listener.listen(endpoint)
        POLLER.loop()
        sys.exit(0)

    connector = BTConnectingPeer(POLLER)
    connector.connect(endpoint)
    POLLER.loop()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
