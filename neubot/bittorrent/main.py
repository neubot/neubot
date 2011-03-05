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

from neubot.bittorrent.stream import BTStream
from neubot.net.stream import Connector
from neubot.net.stream import Listener
from neubot.utils import become_daemon
from neubot.options import OptionParser
from neubot.net.stream import VERBOSER
from neubot.net.stream import MEASURER
from neubot.net.poller import POLLER
from neubot.arcfour import arcfour_new
from neubot.log import LOG


class Upload(object):

    """Responds to requests."""

    def __init__(self, handler, scramble):
        self.handler = handler
        self.scrambler = None
        if scramble:
            self.scrambler = arcfour_new()
        self.interested = False

    def got_request(self, index, begin, length):
        if not self.interested:
            return
        data = "A" * length
        if self.scrambler:
            data = self.scrambler.encrypt(data)
        self.handler.send_piece(index, begin, data)

    def got_interested(self):
        self.interested = True
        self.handler.send_unchoke()

    def got_not_interested(self):
        self.interested = False
        self.handler.send_choke()

class Download(object):

    """Requests missing pieces."""

    def __init__(self, handler):
        self.handler = handler
        self.choked = True

    def got_piece(self, index, begin, length):
        if self.choked:
            return
        self.handler.send_request(index, 0, 1<<15)

    def got_choke(self):
        self.choked = True

    def got_unchoke(self):
        self.choked = False
        for index in range(0, 32):
            self.handler.send_request(index, 0, 1<<15)

class BTConnectingPeer(Connector):

    """Connect to a given BitTorrent peer and controls the
       resulting connection."""

    def __init__(self, poller):
        Connector.__init__(self, poller)
        self.infohash = "".join( ['\xaa']*20 )
        self.my_id = "".join( ['\xaa']*20 )
        self.stream = BTStream
        self.dictionary = {}

    def configure(self, dictionary):
        self.dictionary = dictionary

    def connection_failed(self, exception):
        VERBOSER.connection_failed(self.endpoint, exception, fatal=True)

    def started_connecting(self):
        VERBOSER.started_connecting(self.endpoint)

    def connection_made(self, handler):
        handler.configure(self.dictionary)
        MEASURER.register_stream(handler)
        handler.initialize(self, self.my_id, True)
        handler.download = Download(handler)
        scramble = not self.dictionary.get("obfuscate", False)
        handler.upload = Upload(handler, scramble)

    def connection_handshake_completed(self, handler):
        handler.send_interested()

class BTListeningPeer(Listener):

    """Listens for connections from BitTorrent peers and controls the
       resulting connections."""

    def __init__(self, poller):
        Listener.__init__(self, poller)
        self.infohash = "".join( ['\xaa']*20 )
        self.my_id = "".join( ['\xaa']*20 )
        self.stream = BTStream
        self.dictionary = {}

    def configure(self, dictionary):
        self.dictionary = dictionary

    def started_listening(self):
        VERBOSER.started_listening(self.endpoint)

    def accept_failed(self, exception):
        pass

    def bind_failed(self, exception):
        VERBOSER.connection_failed(self.endpoint, exception, fatal=True)

    def connection_made(self, handler):
        handler.configure(self.dictionary)
        MEASURER.register_stream(handler)
        handler.initialize(self, self.my_id, True)
        handler.download = Download(handler)
        scramble = not self.dictionary.get("obfuscate", False)
        handler.upload = Upload(handler, scramble)

    def connection_handshake_completed(self, handler):
        pass

USAGE = """Neubot bittorrent -- BitTorrent test

Usage: neubot bittorrent [-Vv] [-D macro[=value]] [-f file] [--help]

Options:
    -D macro[=value]   : Set the value of the macro `macro`
    -f file            : Read options from file `file`
    --help             : Print this help screen and exit
    -V                 : Print version number and exit
    -v                 : Run the program in verbose mode

Macros (defaults in square brackets):
    address=addr       : Select address to use                  [127.0.0.1]
    daemonize          : Drop privileges and run in background  [False]
    key=KEY            : Use KEY to initialize ARC4 stream      []
    listen             : Listen for incoming connections        [False]
    obfuscate          : Obfuscate traffic using ARC4           [False]
    port=port          : Select the port to use                 [6881]
    sobuf=size         : Set socket buffer size to `size`       []

"""

VERSION = "Neubot 0.3.5\n"

def main(args):

    conf = OptionParser()
    conf.set_option("bittorrent", "address", "127.0.0.1")
    conf.set_option("bittorrent", "daemonize", "False")
    conf.set_option("bittorrent", "key", "")
    conf.set_option("bittorrent", "listen", "False")
    conf.set_option("bittorrent", "obfuscate", "False")
    conf.set_option("bittorrent", "port", "6881")
    conf.set_option("bittorrent", "sobuf", 0)

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
             LOG.verbose()
             continue

    conf.merge_files()
    conf.merge_environ()
    conf.merge_opts()

    address = conf.get_option("bittorrent", "address")
    daemonize = conf.get_option_bool("bittorrent", "daemonize")
    key = conf.get_option("bittorrent", "key")
    listen = conf.get_option_bool("bittorrent", "listen")
    obfuscate = conf.get_option_bool("bittorrent", "obfuscate")
    port = conf.get_option_uint("bittorrent", "port")
    sobuf = conf.get_option_uint("bittorrent", "sobuf")

    endpoint = (address, port)
    dictionary = {
        "obfuscate": obfuscate,
        "key": key,
    }

    if not (listen and daemonize):
        MEASURER.start()

    if listen:
        if daemonize:
            become_daemon()
        listener = BTListeningPeer(POLLER)
        listener.configure(dictionary)
        listener.listen(endpoint, sobuf=sobuf)
        POLLER.loop()
        sys.exit(0)

    connector = BTConnectingPeer(POLLER)
    connector.configure(dictionary)
    connector.connect(endpoint, sobuf=sobuf)
    POLLER.loop()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
