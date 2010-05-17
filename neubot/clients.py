# neubot/clients.py
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
import socket

import neubot

VERSION = "0.0.3"
TESTNAME = "simple"
TESTURI = "http://127.0.0.1:0/simple"
WANT = [ "http", "latency" ]

class simpleclient:
	def __init__(self, poller, scheme, address, port):
		self.poller = poller
		self.request = neubot.http.message(protocol="HTTP/1.1",
		    uri="/rendez-vous/1.0", method="POST")
		self.request["cache-control"] = "no-cache"
		self.request["connection"] = "close"
		self.request["host"] = address + ":" + port
		self.request["pragma"] = "no-cache"
		info = neubot.rendezvous.clientinfo()
		info.set_version(VERSION)
		info.provide_test(TESTNAME, TESTURI)
		for test in WANT:
			info.accept_test(test)
		octets = str(info)
		self.request["content-type"] = "application/json"
		self.request["content-length"] = str(len(octets))
		self.request.body = StringIO.StringIO(octets)
		neubot.http.prettyprinter(logging.info, "HTTP > ",
		    self.request)
		neubot.rendezvous.prettyprinter(logging.info, "JSON > ", info)
		neubot.http.connector(self, self.poller, address, port,
		    socket.AF_INET, (scheme == "https"))

	def aborted(self, connector):
		logging.error("Connection failed")

	def connected(self, connector, protocol):
		logging.info("Connected to the remote host")
		protocol.attach(self)
		protocol.sendmessage(self.request)

	def closing(self, protocol):
		logging.info("Connection closed")

	def got_message(self, protocol):
		response = protocol.message
		protocol.close()
		response.body.seek(0)
		octets = response.body.read()
		if (response["content-type"] == "application/json"
		    and response.code == "200"):
			todo = neubot.rendezvous.todolist(octets)
			neubot.rendezvous.prettyprinter(logging.info,
			    "JSON < ", todo)

	def got_metadata(self, protocol):
		response = protocol.message
		neubot.http.prettyprinter(logging.info, "HTTP < ", response)
		response.body = StringIO.StringIO()

	def is_message_unbounded(self, protocol):
		return (neubot.http.response_unbounded(self.request,
		    protocol.message))

	def message_sent(self, protocol):
		logging.info("Message sent")
