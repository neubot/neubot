# neubot/api_client.py

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

import types
import getopt
import time
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.http.messages import Message
from neubot.http.clients import ClientController
from neubot.http.clients import Client
from neubot.net.poller import POLLER
from neubot.compat import json
from neubot.options import OptionParser
from neubot.log import LOG


class APIStateTracker(ClientController):

    """Polls the state of the Neubot daemon and prints the JSON
       object representing the state on the standard output.

       Subclasses might want to override the method that prints
       to stdout, in order to implement something smarter.

       This class allows the controller to live into another
       thread of execution, and implements a safe mechanism that
       allows to interrupt the polling."""

    def __init__(self, address, port):
        self.timestamp = 0
        self.uri = "http://%s:%s/api/state?t=" % (address, port)
        self.stop = False

    # Do not assume that the controller lives in the same thread
    # of execution we live in.  So, run in a loop and provide a mean
    # to force to break out of the loop: the controlling code just
    # need to call interrupt().

    def interrupt(self):
        self.stop = True

    def loop(self):
        while not self.stop:
            self.start_transaction()
            POLLER.loop()
            # We should land here on errors only
            time.sleep(3)

    def start_transaction(self, client=None):
        request = Message()
        uri = self.uri + str(self.timestamp)
        request.compose(method="GET", uri=uri)
        if not client:
            client = Client(self)
        client.sendrecv(request)

    def got_response(self, client, request, response):
        try:
            self.check_response(response)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            LOG.exception()
            time.sleep(3)
        self.start_transaction(client)

    def check_response(self, response):

        if response.code != "200":
            raise ValueError("Bad HTTP response code")
        if response["content-type"] != "application/json":
            raise ValueError("Unexpected contenty type")

        octets = response.body.read()
        dictionary = json.loads(octets)

        LOG.debug("APIStateTracker: received JSON: " +
            json.dumps(dictionary, ensure_ascii=True))

        if not "events" in dictionary:
            return

        events = dictionary["events"]
        current = dictionary["current"]
        t = dictionary["t"]

        if not type(t) == types.IntType and not type(t) == types.LongType:
            raise ValueError("Invalid type for current event time")
        if t < 0:
            raise ValueError("Invalid value for current event time")

        self.timestamp = t
        self.process_dictionary(dictionary)

    def process_dictionary(self, dictionary):
        octets = json.dumps(dictionary)
        sys.stdout.write(octets)
        sys.stdout.write("\n\n")


USAGE = """Neubot api_client -- Minimal client for JSON API

Usage: neubot api_client [-Vv] [-D macro[=value]] [-f file] [--help]

Options:
    -D macro[=value]   : Set the value of the macro `macro`
    -f file            : Read options from file `file`
    --help             : Print this help screen and exit
    -V                 : Print version number and exit
    -v                 : Run the program in verbose mode

Macros (defaults in square brackets):
    address=addr       : Select the address to use                 [127.0.0.1]
    port=port          : Select the port to use                    [9774]

"""

VERSION = "Neubot 0.3.6\n"

def main(args):

    conf = OptionParser()
    conf.set_option("api_client", "address", "127.0.0.1")
    conf.set_option("api_client", "port", "9774")

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
             conf.register_opt(value, "api_client")
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

    address = conf.get_option("api_client", "address")
    port = conf.get_option("api_client", "port")

    client = APIStateTracker(address, port)
    client.loop()

if __name__ == "__main__":
    main(sys.argv)
