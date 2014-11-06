# net/handler.py

#
# Copyright (c) 2010-2012, 2014
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

""" Network events handler """

from neubot import utils_net

from .connector import Connector
from .listener import Listener

class Handler(object):
    """ Network events handler """

    def __init__(self, poller):
        self._poller = poller
        self._conf = {}

    def configure(self, conf):
        """ Attach this object to its configuration """
        self._conf = conf

    def listen(self, endpoint):
        """ Listen at the specified endpoint """
        # API change: we now ignore the global CONFIG
        sockets = utils_net.listen(endpoint, self._conf)
        if not sockets:
            self.bind_failed(endpoint)
            return
        for sock in sockets:
            listener = Listener(self._poller, self, sock, endpoint)
            listener.listen()

    def bind_failed(self, epnt):
        """ Override this method in derived classes """

    def started_listening(self, listener):
        """ Override this method in derived classes """

    def accept_failed(self, listener, exception):
        """ Override this method in derived classes """

    def connect(self, endpoint, count=1):
        """ Connect to the specified endpoint """
        # API note: we keep the count argument for compatibility
        if count > 1:
            raise RuntimeError("connect() multiple sockets: not implemented")
        connector = Connector(self._poller, self)
        connector.connect(endpoint, self._conf)

    def connection_failed(self, connector, exception):
        """ Override this method in derived classes """

    def started_connecting(self, connector):
        """ Override this method in derived classes """

    def connection_made(self, sock, endpoint, rtt):
        """ Override this method on derived classes """

    def connection_lost(self, stream):
        """ Override this method on derived classes """
