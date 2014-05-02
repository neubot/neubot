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

# Regression test for neubot/pollable.py PollableConnector

import logging
import sys
import time

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.pollable import PollableConnector
from neubot.poller import POLLER

class MyConnector(PollableConnector):
    def handle_connect(self, error):
        if error != 0:
            logging.warning("MyConnector: cannot connect")
            return
        sock = self.get_socket()
        filenum = sock.fileno()
        rtt = self.get_rtt()
        logging.debug("MyConnector: connection made %d %f", filenum, rtt)
        sock.close()

def main():
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    for port in ("80", "81"):
        MyConnector.connect(POLLER, "PF_UNSPEC6",
          "neubot.mlab.mlab1.trn01.measurement-lab.org", port)
    POLLER.loop()

if __name__ == "__main__":
    main()
