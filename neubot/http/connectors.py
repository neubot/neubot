# neubot/http/connectors.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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

import logging
import socket
import ssl
import sys

import neubot

class connector:
	def __init__(self, application, poller, address, port,
	    family=socket.AF_INET, secure=False):
		self.application = application
		self.poller = poller
		self.poller.register_initializer(self.init)
		self.address = address
		self.port = port
		self.family = family
		self.secure = secure
		self.socket = None

	def init(self):
		self.socket = neubot.network.connect(self.family,
		    self.address, self.port)
		self.poller.set_writable(self)

	def closing(self):
		self.application.aborted(self)
		self.application = None

	def fileno(self):
		return (self.socket.fileno())

	def readable(self):
		pass

	def writable(self):
		self.poller.unset_writable(self)
		self.socket.getpeername()		# Connected?
		if (self.secure):
			ssl_socket = ssl.wrap_socket(self.socket,
			    do_handshake_on_connect=False)
			connection = neubot.network.ssl_connection(
			    self.poller, ssl_socket)
		else:
			connection = neubot.network.socket_connection(
			    self.poller, self.socket)
		adaptor = neubot.http.adaptor(connection)
		protocol = neubot.http.protocol(adaptor)
		self.application.connected(self, protocol)
