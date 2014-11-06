# sample/chargen.py

#
# Copyright (c) 2014
#   Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#   and Simone Basso <bassosimone@gmail.com>
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

""" Chargen """

import logging

from ..net import HandlerEx
from ..net import StreamEx

BUFFER = "A" * 8000

class ChargenClient(HandlerEx):
    """ Chargen client """

    def __init__(self, poller, endpoint, conf=None):
        HandlerEx.__init__(self, poller)
        self._poller = poller
        self._endpoint = endpoint
        self._conf = conf
        logging.debug("chargen: connecting to %s:%s", self._endpoint[0],
                      self._endpoint[1])
        self.connect(self._endpoint)

    def connection_made(self, sock, endpoint, rtt):
        logging.debug("chargen: connection to %s:%s established",
                      endpoint[0], endpoint[1])
        stream = StreamEx(self._poller, self, sock)
        stream.write(BUFFER)

    def can_send(self, stream):
        stream.write(BUFFER)

    def connection_lost(self, stream):
        logging.debug("chargen: lost connection %s", stream)
