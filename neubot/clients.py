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

VERSION = "0.0.4"
TESTNAME = "simple"
TESTURI = "http://127.0.0.1:0/simple"
WANT = [ "http", "latency" ]

class simpleclient:
	def __init__(self, poller, scheme, address, port):
		logging.info("Begin rendez-vous procedure")
		self.poller = poller
		self.scheme = scheme
		self.address = address
		self.port = port
		self.request = None
		neubot.http.connector(self, self.poller, address, port,
		    socket.AF_INET, (scheme == "https"))

	def __del__(self):
		logging.info("End rendez-vous procedure")

	def aborted(self, connector):
		logging.error("Connection to '%s:%s' failed" % (
		    self.address, self.port))

	def connected(self, connector, protocol):
		logging.info("We're connected to '%s'" % protocol.peername)
		protocol.attach(self)
		logging.info("Pretty-printing the request we will send")
		self.request = neubot.http.message(protocol="HTTP/1.1",
		    uri="/rendez-vous/1.0", method="POST")
		self.request["date"] = neubot.http.date()
		self.request["cache-control"] = "no-cache"
		self.request["connection"] = "close"
		self.request["host"] = self.address + ":" + self.port
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
		neubot.http.prettyprinter(logging.info, "  ", self.request)
		neubot.rendezvous.prettyprinter(logging.info, "  ", info)
		logging.info("Start sending the request")
		protocol.sendmessage(self.request)

	def closing(self, protocol):
		logging.info("Connection to '%s' closed" % protocol.peername)

	def got_message(self, protocol):
		response = protocol.message
		response.body.seek(0)
		octets = response.body.read()
		todo = neubot.rendezvous.todolist(octets)
		neubot.rendezvous.prettyprinter(logging.info, "  ", todo)
		protocol.close()

	def got_metadata(self, protocol):
		logging.info("Pretty-printing response we received")
		response = protocol.message
		neubot.http.prettyprinter(logging.info, "  ", response)
		response.body = StringIO.StringIO()
		if (response["content-type"] != "application/json"
		    or response.code != "200"):
			logging.error("Unexpected response")
			protocol.close()
			return

	def is_message_unbounded(self, protocol):
		return (neubot.http.response_unbounded(self.request,
		    protocol.message))

	def message_sent(self, protocol):
		logging.info("Done sending the request")
		logging.info("Now waiting for the response")
