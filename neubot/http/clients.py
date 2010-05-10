# neubot/http/clients.py
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

#
# DEPRECATED -- use neubot/http/connectors.py instead
#

import logging
import socket
import ssl
import sys

import neubot

CONNECTING = 0
SENDINGREQUEST = 1
REQUESTSENT = 2
RECEIVEDHEADERS = 3
RESPONSECOMPLETE = 4

class client:
	def __init__(self, poller, method, uri, family=socket.AF_INET,
	    prettyprint=False, outfile=sys.stdout, controller=None):
		self.poller = poller
		(scheme, address, port, pathquery) = neubot.http.urlsplit(uri)
		self.request = neubot.http.message()
		self.request.method = method
		self.request.uri = pathquery 
		self.request.protocol = "HTTP/1.1"
		self.request["connection"] = "close"
		self.request["pragma"] = "no-cache"
		self.request["cache-control"] = "no-cache"
		self.request["host"] = address + ":" + port
		self.request["user-agent"] = "Neubot/0.0 Python/2.6"
		self.use_ssl = (scheme == "https")
		self.prettyprint = prettyprint
		self.outfile = outfile
		self.state = CONNECTING
		self.unbounded = False
		self.controller = controller
		logging.info("Connecting to %s:%s" % (address, port))
		self.socket = neubot.network.connect(family, address, port)
		self.poller.set_writable(self)

	def closing(self):
		if (self.state == CONNECTING):
			logging.warning("Could not connect")
		elif (self.state == SENDINGREQUEST):
			logging.warning("Could not send request")
		elif (self.state == REQUESTSENT):
			logging.warning("Response not received")
		elif (self.state == RECEIVEDHEADERS):
			if (not self.unbounded):
				logging.warning("Connection closed prematurely")
		else:
			pass
		if (self.controller):
			self.controller.closing(self)

	#
	# Connection in progress
	#

	def fileno(self):
		return (self.socket.fileno())

	def readable(self):
		pass

	def writable(self):
		self.poller.unset_writable(self)
		self.socket.getpeername()		# Connected?
		if (self.use_ssl):
			ssl_socket = ssl.wrap_socket(self.socket,
			    do_handshake_on_connect=False)
			conn = neubot.network.ssl_connection(self.poller,
			    ssl_socket)
		else:
			conn = neubot.network.socket_connection(self.poller,
			    self.socket)
		adaptor = neubot.http.adaptor(conn)
		self.protocol = neubot.http.protocol(adaptor)
		self.protocol.attach(self)
		self.protocol.sendmessage(self.request)
		self.socket = None
		self.state = SENDINGREQUEST
		addrport = self.request["host"]
		logging.info("Sending request to %s" % addrport)

	#
	# Connection established
	#

	def got_message(self):
		self.state = RESPONSECOMPLETE
		logging.info("Received response body, closing connection")
		self.protocol.close()
		if (self.controller):
			self.controller.got_message(self)

	def got_metadata(self):
		logging.info("Received response headers")
		self.state = RECEIVEDHEADERS
		response = self.protocol.message
		response.body = self.outfile
		if (self.prettyprint):
			neubot.http.prettyprint(sys.stderr,
			    "> ", response)
		if (self.controller):
			self.controller.got_metadata(self)

	def is_message_unbounded(self):
		response = self.protocol.message
		self.unbounded = neubot.http.response_unbounded(self.request,
		    response)
		return (self.unbounded)

	def message_sent(self):
		logging.info("Request sent, waiting for response")
		self.state = REQUESTSENT
		if (self.prettyprint):
			neubot.http.prettyprint(sys.stderr,
			    "< ", self.request)
