# neubot/testing/publish.py
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
import getopt
import logging
import os
import socket
import sys

import neubot

class Publisher:
	def __init__(self, poller, address, port, family=socket.AF_INET,
	    secure=False, certfile=None, prettyprint=False, outfile=sys.stdout):
		self.poller = poller
		neubot.http.acceptor(self, self.poller, address, port,
		    family, secure, certfile)
		self.prettyprint = prettyprint
		self.outfile = outfile
		self.mustclose = {}
		self.names = []

	def closing(self, protocol):
		if (self.mustclose.has_key(protocol)):
			del self.mustclose[protocol]

	def got_client(self, protocol):
		protocol.attach(self)

	def got_message(self, protocol):
		request = protocol.message
		response = neubot.http.message(protocol="HTTP/1.1")
		response["cache-control"] = "no-cache"
		if (request.protocol == "HTTP/1.0" or
		    request["connection"] == "close"):
			self.mustclose[protocol] = True
			response["connection"] = "close"
		if (request.method in ["POST", "PUT"]):
			response.code, response.reason = "204", "No content"
		elif (request.method in ["GET", "HEAD"]):
			path = request.uri[1:]			# XXX
			f = None
			try:
				f = open(path, "rb")
			except:
				pass
			if (f):
				response.code, response.reason = "200", "Ok"
			else:
				response.code = "404"
				response.reason = "Not Found"
				f = StringIO.StringIO("Not Found\r\n")
			f.seek(0, os.SEEK_END)
			length = f.tell()
			f.seek(0, os.SEEK_SET)
			response["content-length"] = str(length)
			response["content-type"] = "text/plain"
			if (request.method == "GET"):
				response.body = f
		else:
			response.code = "405"
			response.reason = "Method Not Allowed"
			response["allow"] = "GET, HEAD, POST, PUT"
			self.mustclose[protocol] = True
			response["connection"] = "close"
		protocol.sendmessage(response)
		if (self.prettyprint):
			neubot.http.prettyprint(sys.stderr,
			    "> ", response)

	def got_metadata(self, protocol):
		request = protocol.message
		if (self.prettyprint):
			neubot.http.prettyprint(sys.stderr,
			    "< ", request)
		if (request["expect"] == "100-continue"):
			response = neubot.http.message(protocol="HTTP/1.1",
			    code="100", reason="Continue")
			protocol.sendmessage(response)
			if (self.prettyprint):
				neubot.http.prettyprint(sys.stderr,
				    "> ", response)
		request.body = self.outfile		# Yes, always

	def is_message_unbounded(self, protocol):
		return (False)

	def message_sent(self, protocol):
		if (self.mustclose.has_key(protocol)):
			protocol.close()

	def publish(self, name):
		if (not name in self.names):
			self.names.append(name)

USAGE = "python %s [-46v] [-A address] [-p port] [-S certfile] [file ...]\n"

def main():
	address = "0.0.0.0"
	family = socket.AF_INET
	port = "8080"
	verbose = False
	outfile = sys.stdout
	certfile = None
	try:
		opts, files = getopt.getopt(sys.argv[1:], "46A:p:S:v")
	except getopt.error:
		sys.stderr.write(USAGE % sys.argv[0])
		sys.exit(1)
	for opt, arg in opts:
		if (opt == "-4"):
			family = socket.AF_INET
		elif (opt == "-6"):
			family = socket.AF_INET6
		elif (opt == "-A"):
			address = arg
		elif (opt == "-p"):
			port = arg
		elif (opt == "-S"):
			certfile = arg
		elif (opt == "-v"):
			verbose = True
	if (verbose):
		logger = logging.getLogger()
		logger.setLevel(logging.DEBUG)
	poller = neubot.network.poller()
	publisher = Publisher(poller, address, port, family, certfile != None,
	    certfile, verbose, outfile)
	for name in files:
		publisher.publish(name)
	poller.loop()
	sys.exit(0)

if (__name__ == "__main__"):
	main()
