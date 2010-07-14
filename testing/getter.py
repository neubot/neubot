# testing/getter.py
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

import getopt
import logging
import socket
import sys

import neubot

class Getter:
	def __init__(self, poller, outfile=sys.stdout, prettyprint=False,
	    family=socket.AF_INET):
		self.poller = poller
		self.outfile = outfile
		self.prettyprint = prettyprint
		self.family = family
		self.connectors = {}
		self.protocols = {}

	def aborted(self, connector):
		del self.connectors[connector]

	def connected(self, connector, protocol):
		request = self.connectors[connector]
		del self.connectors[connector]
		protocol.attach(self)
		self.protocols[protocol] = request
		protocol.sendmessage(request)

	def closing(self, protocol):
		del self.protocols[protocol]

	def get(self, uri):
		(scheme, address, port, pathquery) = neubot.http.urlsplit(uri)
		request = neubot.http.message(method="GET", uri=pathquery,
		    protocol="HTTP/1.1")
		request["date"] = neubot.http.date()
		request["connection"] = "close"
		request["pragma"] = "no-cache"
		request["cache-control"] = "no-cache"
		request["host"] = address + ":" + port
		connector = neubot.http.connector(self, self.poller,
		    address, port, self.family, (scheme == "https"))
		self.connectors[connector] = request

	def got_message(self, protocol):
		protocol.close()

	def got_metadata(self, protocol):
		response = protocol.message
		response.body = self.outfile
		if (self.prettyprint):
			neubot.http.prettyprinter(sys.stderr.write,
			    "< ", response, eol="\r\n")

	def is_message_unbounded(self, protocol):
		request = self.protocols[protocol]
		response = protocol.message
		unbounded = neubot.http.response_unbounded(request, response)
		return (unbounded)

	def message_sent(self, protocol):
		request = self.protocols[protocol]
		if (self.prettyprint):
			neubot.http.prettyprinter(sys.stderr.write,
			    "> ", request, eol="\r\n")
		protocol.recvmessage()

USAGE = "Usage: python %s [-46v] uri [uri ...]\n"

def main():
	family = socket.AF_UNSPEC
	verbose = False
	try:
		opts, uris = getopt.getopt(sys.argv[1:], "46v")
	except getopt.error:
		sys.stderr.write(USAGE % sys.argv[0])
		sys.exit(1)
	for opt, arg in opts:
		if (opt == "-4"):
			family = socket.AF_INET
		elif (opt == "-6"):
			family = socket.AF_INET6
		elif (opt == "-v"):
			verbose = True
	if (len(uris) == 0):
		sys.stderr.write(USAGE % sys.argv[0])
		sys.exit(1)
	if (verbose):
		logger = logging.getLogger()
		logger.setLevel(logging.DEBUG)
	poller = neubot.network.poller()
	getter = Getter(poller, prettyprint=verbose, family=family)
	for uri in uris:
		getter.get(uri)
	poller.loop()
	sys.exit(0)

if (__name__ == "__main__"):
	main()
