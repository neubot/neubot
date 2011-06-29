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

import getopt
import random
import sys

sys.path.insert(0, ".")

from neubot.log import LOG
from neubot.database import DATABASE
from neubot.net.poller import POLLER
from neubot.notify import NOTIFIER
from neubot.speedtest.client import ClientSpeedtest

#
# XXX Odd to import ServerSpeedtest from negotiate but for now
# it's how the whole thing works.  For sure some future round of
# refactoring will give justice to this inconsistency too.
#
from neubot.speedtest.negotiate import ServerSpeedtest

#
# Here the idea is... let's stress-test the algorithm that
# manages the queue and see how well it deals with lost connections
# from clients.  Some preliminary tests shows that we can do
# something better on that dept.
#
class MyClientSpeedtest(ClientSpeedtest):

    def got_response_headers(self, stream, request, response):
        if random.random() >= 0.1:
            return ClientSpeedtest.got_response_headers(self, stream,
                     request, response)
        else:
            return False

    def got_response(self, stream, request, response):
        if random.random() >= 0.01:
            ClientSpeedtest.got_response(self, stream, request, response)
        else:
            stream.close()

def speedtest_again(event=None, context=None):
    NOTIFIER.subscribe("testdone", speedtest_again, None)
    client = MyClientSpeedtest(POLLER)
    client.configure({"speedtest.client.uri": "http://127.0.0.1:8080/"})
    client.connect_uri()

def main():
    Sflag = False

    options, arguments = getopt.getopt(sys.argv[1:], "S")
    for key, value in options:
        if key == "-S":
            Sflag = True

    # don't clobber my local database
    DATABASE.set_path(":memory:")
    DATABASE.connect()

    if Sflag:
        server = ServerSpeedtest(POLLER)
        server.configure({"speedtest.negotiate.daemonize": False})
        server.listen(("127.0.0.1", 8080))

    else:
        speedtest_again()

    POLLER.loop()

if __name__ == "__main__":
    main()
