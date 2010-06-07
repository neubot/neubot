# neubot/http/acceptors.py
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

import socket
import ssl

import neubot

class acceptor:
	def __init__(self, application, poller, address, port,
	    family=socket.AF_INET, secure=False, certfile=None):
		self.application = application
		self.poller = poller
		self.poller.register_func(self.init)
		self.address = address
		self.port = port
		self.family = family
		self.secure = secure
		self.certfile = certfile
		self.socket = None

	def __str__(self):
		return self.address + ":" + self.port

	def init(self):
		try:
			self.socket = neubot.network.listen(self.family,
			    self.address, self.port)
			self.poller.set_readable(self)
			self.application.listening(self)
		except:
			self.application.aborted(self)
			self.application = None

	def closing(self):
		self.socket.close()

	def fileno(self):
		return (self.socket.fileno())

	def readable(self):
		try:
			socket = neubot.network.accept(self.socket)
			sockname = socket.getsockname()
			peername = socket.getpeername()
			if (self.secure):
				ssl_socket = ssl.wrap_socket(socket,
				    do_handshake_on_connect=False,
				    certfile=self.certfile, server_side=True)
				connection = neubot.network.ssl_connection(
				    self.poller, ssl_socket, sockname, peername)
			else:
				connection = neubot.network.socket_connection(
				    self.poller, socket, sockname, peername)
			adaptor = neubot.http.adaptor(connection)
			protocol = neubot.http.protocol(adaptor)
			self.application.got_client(protocol)
		except:
			neubot.utils.prettyprint_exception()

	def writable(self):
		pass
