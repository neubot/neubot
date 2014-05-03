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

# Regression test for neubot/connector.py

import logging
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.connector import Connector
from neubot.poller import POLLER

class Parent(object):
    def handle_connect(self, connector, sock, rtt, sslconfig, extra):
        logging.debug("handle_connect: %s %s, %f, %s, %s", connector, sock,
          rtt, sslconfig, extra)

    def handle_connect_error(self, connector):
        logging.debug("handle_connect_error: %s", connector)

def main():
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    parent = Parent()
    Connector(parent, ("www.neubot.org www2.neubot.org", 81), True, 0, {})
    Connector(parent, ("www.nonexistent", 81), True, 0, {})
    Connector(parent, ("www.nexacenter.org", 80), True, 0, {})
    POLLER.loop()

if __name__ == "__main__":
    main()
