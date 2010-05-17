# neubot/servers.py
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

import StringIO
import logging

import neubot

AVAILABLE = {
	"bittorrent": "http://whitespider.polito.it:9773/bittorrent",
	"http": "http://whitespider.polito.it:9773/http",
	"latency": "http://whitespider.polito.it:9773/latency"
}

VERSION = "0.0.3"
URI = "http://whitespider.polito.it:8080/neubot-" + VERSION + ".exe"

class simpleserver:
	def __init__(self, poller, family, address, port):
		self.poller = poller
		neubot.http.acceptor(self, self.poller, address, port,
		    family, False, None)

	def closing(self, protocol):
		logging.info("Closing connection")

	def got_client(self, protocol):
		logging.info("Got connection")
		protocol.attach(self)

	def got_message(self, protocol):
		request = protocol.message
		if (request.uri == "/rendez-vous/1.0"):
			if (request.method == "POST"):
				request.body.seek(0)
				octets = request.body.read()
				info = neubot.rendezvous.clientinfo(octets)
				neubot.rendezvous.prettyprinter(logging.info,
				    "JSON < ", info)
				logging.info("Analyzing client info")
				logging.info("Preparing per-client todo list")
				todo = neubot.rendezvous.todolist()
				todo.set_versioninfo(VERSION, URI)
				for name, uri in AVAILABLE.items():
					todo.add_available(name, uri)
				logging.info("Preparing HTTP response")
				response = neubot.http.message(reason="Ok",
				    code="200", protocol="HTTP/1.1")
				response["cache-control"] = "no-cache"
				response["connection"] = "close"
				response["content-type"] = "application/json"
				octets = str(todo)
				response["content-length"] = str(len(octets))
				response.body = StringIO.StringIO(octets)
				neubot.http.prettyprinter(logging.info,
				    "HTTP > ", response)
				neubot.rendezvous.prettyprinter(logging.info,
				    "JSON > ", todo)
			else:
				response = neubot.http.message(code="405",
				    reason="Method Not Allowed",
				    protocol="HTTP/1.1")
				response["allow"] = "POST"
				response["cache-control"] = "no-cache"
				response["connection"] = "close"
				neubot.http.prettyprinter(logging.info,
				    "HTTP > ", response)
		else:
			response = neubot.http.message(protocol="HTTP/1.1",
			    code="404", reason="Not Found")
			response["cache-control"] = "no-cache"
			response["connection"] = "close"
			neubot.http.prettyprinter(logging.info,
			    "HTTP > ", response)
		protocol.sendmessage(response)

	def got_metadata(self, protocol):
		request = protocol.message
		neubot.http.prettyprinter(logging.info, "HTTP < ", request)
		request.body = StringIO.StringIO()

	def is_message_unbounded(self, protocol):
		return (False)

	def message_sent(self, protocol):
		protocol.close()
