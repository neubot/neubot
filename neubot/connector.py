# neubot/connector.py

#
# Copyright (c) 2010-2012 Simone Basso <bassosimone@gmail.com>,
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

#
# pylint: disable = missing-docstring
# Adapted from neubot/net/stream.py
# Python3-ready: yes
#

import logging

from neubot.defer import Deferred
from neubot.pollable import StreamConnector
from neubot.poller import POLLER

class ChildConnector(StreamConnector):

    def __init__(self):
        StreamConnector.__init__(self)
        self.parent = None

    def handle_connect(self, error):
        self.parent.child_completed_(self, error)

class Connector(object):

    def __init__(self, parent, endpoint, prefer_ipv6, sslconfig, extra):

        self.parent = parent
        self.endpoint = endpoint
        self.prefer_ipv6 = prefer_ipv6
        self.sslconfig = sslconfig
        self.extra = extra

        self.aterror = Deferred()
        self.aterror.add_callback(self.parent.handle_connect_error)

        self._connect()

    def __repr__(self):
        return str(self.endpoint)

    def register_errfunc(self, func):
        self.aterror.add_callback(func)

    def _connection_failed(self):
        self.aterror.callback_each_np(self)

    def _connect(self):

        # Note that connect() also accepts a boolean family
        child = ChildConnector.connect(POLLER, self.prefer_ipv6,
          self.endpoint[0], self.endpoint[1])
        if not child:
            self._connection_failed()
            return

        child.parent = self

    def child_completed_(self, child, error):
        if error:
            self._connection_failed()
            return
        deferred = Deferred()
        deferred.add_callback(self._handle_connect)
        deferred.add_errback(self._handle_connect_error)
        deferred.callback(child)

    def _handle_connect(self, child):
        self.parent.handle_connect(self, child.get_socket(), child.get_rtt(),
          self.sslconfig, self.extra)

    def _handle_connect_error(self, error):
        logging.warning('connector: connect() error: %s', str(error))
        self._connection_failed()
