# sample/discard.py

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

""" Discard """

import logging

from ..net import HandlerEx

class DiscardServer(HandlerEx):
    """ Discard server """

    def __init__(self, poller, endpoint, conf=None):
        HandlerEx.__init__(self, poller, conf)
        self._endpoint = endpoint
        logging.debug("discard: listening at %s:%s", self._endpoint[0],
                      self._endpoint[1])
        self.listen(self._endpoint)

    def connection_established(self, stream, rtt):
        logging.debug("discard: connection %s established", stream)
        stream.start_recv()

    def got_data(self, stream, data):
        stream.start_recv()

    def connection_lost(self, stream):
        logging.debug("discard: lost connection %s", stream)
