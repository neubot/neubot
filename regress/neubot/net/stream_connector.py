#!/usr/bin/env python

#
# Copyright (c) 2014
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>.
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

# Regression test for neubot/net/stream.py:Connector

import logging
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.net.stream import StreamHandler
from neubot.poller import POLLER

from neubot import log

class Parent(StreamHandler):
    def connection_made(self, sock, endpoint, rtt):
        logging.debug("handle_connect: %s, %s, %f", sock, endpoint, rtt)

    def connection_failed(self, connector, exception):
        logging.debug("handle_connect_error: %s %s", connector, exception)

def main():
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    log.set_verbose()
    parent = Parent(POLLER)
    parent.connect(("www.neubot.org www2.neubot.org", 81), 2)
    parent.connect(("www.neubot.org www2.neubot.org", 80), 2)
    POLLER.loop()

if __name__ == "__main__":
    main()
