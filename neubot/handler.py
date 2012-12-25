# neubot/handler.py

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

''' Handles poller events '''

# Adapted from neubot/net/stream.py
# Python3-ready: yes

from neubot.connector import Connector
from neubot.listener import Listener

from neubot import utils_net

class Handler(object):

    ''' Event handler '''

    # Inspired by BitTorrent handle class

    def listen(self, endpoint, prefer_ipv6, sslconfig, sslcert):
        ''' Listen() at endpoint '''
        sockets = utils_net.listen(endpoint, prefer_ipv6)
        if not sockets:
            self.handle_listen_error(endpoint)
            return
        for sock in sockets:
            Listener(self, sock, endpoint, sslconfig, sslcert)

    def handle_listen_error(self, endpoint):
        ''' Handle the LISTEN_ERROR event '''

    def handle_listen(self, listener):
        ''' Handle the LISTEN event '''

    def handle_listen_close(self, listener):
        ''' Handle the LISTEN_CLOSE event '''

    def handle_accept(self, listener, sock, sslconfig, sslcert):
        ''' Handle the ACCEPT event '''

    def handle_accept_error(self, listener):
        ''' Handle the ACCEPT_ERROR event '''

    def connect(self, endpoint, prefer_ipv6, sslconfig, extra):
        ''' Connect() to endpoint '''
        return Connector(self, endpoint, prefer_ipv6, sslconfig, extra)

    def handle_connect_error(self, connector):
        ''' Handle the CONNECT_ERROR event '''

    def handle_connect(self, connector, sock, rtt, sslconfig, extra):
        ''' Handle the CONNECT event '''

    def handle_close(self, stream):
        ''' Handle the CLOSE event '''
