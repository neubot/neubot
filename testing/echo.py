# neubot/testing/echo.py
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

class echoer:
	def __init__(self, connection):
		self.connection = connection
		self.sendbuff = neubot.network.sendbuff()
		self.connection.attach(self)
		self.connection.set_readable()

	def closing(self):
		self.connection = None
		self.sendbuff = None

	def readable(self):
		piece = self.connection.recv(8000)
		self.sendbuff.set_content(piece)
		self.connection.set_writable()
		self.connection.unset_readable()

	def writable(self):
		content = self.sendbuff.get_content()
		count = self.connection.send(content)
		self.sendbuff.advance(count)
		if (len(self.sendbuff) == 0):
			self.connection.unset_writable()
			self.connection.set_readable()

class listener:
	def __init__(self, poller, family, address, port):
		self.poller = poller
		self.poller.register_func(self.init)
		self.family = family
		self.address = address
		self.port = port

	def init(self):
		self.sock = neubot.network.listen(self.family,
		    self.address, self.port)
		self.poller.set_readable(self)

	def fileno(self):
		return (self.sock.fileno())

	def closing(self):
		self.sock = None

	def readable(self):
		try:
			s = neubot.network.accept(self.sock)
			sockname = s.getsockname()
			peername = s.getpeername()
			connection = neubot.network.socket_connection(
			    self.poller, s, sockname, peername)
			echoer(connection)
		except:
			neubot.utils.prettyprint_exception()

	def writable(self):
		pass

USAGE = "Usage: python %s [-46v] [-A address] [-p port]\n"

def main():
	family = socket.AF_UNSPEC
	address = "127.0.0.1"
	port = "10007"
	verbose = False
	try:
		opts, args = getopt.getopt(sys.argv[1:], "46A:p:v")
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
		elif (opt == "-v"):
			verbose = True
	if (len(args) != 0):
		sys.stderr.write(USAGE % sys.argv[0])
		sys.exit(1)
	if (verbose):
		logger = logging.getLogger()
		logger.setLevel(logging.DEBUG)
	poller = neubot.network.poller()
	listener(poller, family, address, port)
	poller.loop()
	sys.exit(0)

if (__name__ == "__main__"):
	main()
