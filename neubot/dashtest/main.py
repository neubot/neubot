# neubot/dashtest/main.py

#
# Copyright (c) 2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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

""" The DASH test main """

#
# Python3-ready: yes
#

import getopt
import logging
import socket
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.dashtest import client
from neubot.dashtest import handler
from neubot.dashtest import server

from neubot.poller import POLLER

def main(args):
    """ The main function """

    family = socket.AF_INET
    address = "127.0.0.1"
    listen = 0
    port = "8080"
    level = logging.WARNING

    try:
        options, arguments = getopt.getopt(args[1:], "6A:lp:v")
    except getopt.error:
        sys.exit("usage: neubot dashtest [-6lv] [-A address] [-p port]")
    if arguments:
        sys.exit("usage: neubot dashtest [-6lv] [-A address] [-p port]")

    for name, value in options:
        if name == "-6":
            family = socket.AF_INET6
        elif name == "-A":
            address = value
        elif name == "-l":
            listen = 1
        elif name == "-p":
            port = value
        elif name == "-v":
            level = logging.DEBUG

    logging.basicConfig(format="%(message)s", level=level)

    message = {
               "address": address,
               "port": int(port),
               "family": family,
              }

    if not listen:
        channel = "dashtest/client"
        message["authorization"] = "notneeded"
        message["reply_to"] = "nothing"
        message["host"] = message["address"]
    else:
        channel = "dashtest/server"

    client.setup(POLLER)
    handler.setup(POLLER)
    server.setup(POLLER)

    POLLER.send_message(channel, message)

    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
