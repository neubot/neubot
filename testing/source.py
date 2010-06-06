# neubot/testing/source.py
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
import os
import socket
import sys

import neubot

class sender:
	def __init__(self, connection, filelike):
		self.connection = connection
		self.sendbuff = neubot.network.sendbuff()
		self.connection.attach(self)
		self.connection.set_writable()
		self.filelike = filelike

	def closing(self):
		self.connection = None
		self.writer = None

	def readable(self):
		pass

	def writable(self):
		if (len(self.sendbuff) == 0):
			piece = self.filelike.read()
			if (piece == ""):
				self.connection.close()
				return
			self.sendbuff.set_content(piece)
		content = self.sendbuff.get_content()
		count = self.connection.send(content)
		self.sendbuff.advance(count)

class connector:
	def __init__(self, poller, family, address, port, filelike):
		self.poller = poller
		self.poller.register_initializer(self.init)
		self.family = family
		self.address = address
		self.port = port
		self.filelike = filelike

	def init(self):
		sock = neubot.network.connect(self.family,
		    self.address, self.port)
		sockname = sock.getsockname()
		peername = sock.getpeername()
		connection = neubot.network.socket_connection(
		    self.poller, sock, sockname, peername)
		sender(connection, self.filelike)

class Afile:
	def __init__(self, size=8000):
		i = 0
		lst = []
		while (i < size):
			lst.append("A")
			i = i + 1
		self.buffer = "".join(lst)

	def read(self):
		return (self.buffer)

class randomfile:
	def __init__(self, size=8000):
		self.size = size

	def read(self):
		return (os.urandom(self.size))

class realfile:
	def __init__(self, ffile, size=8000):
		self.filelike = open(ffile, "rb")
		self.size = size

	def read(self):
		return (self.filelike.read(self.size))

USAGE = "Usage: python %s [-46Rv] [-A address] [-f file] [-p port]\n"

def main():
	family = socket.AF_UNSPEC
	address = "127.0.0.1"
	port = "10009"
	verbose = False
	ffile = None
	rand = False
	try:
		opts, args = getopt.getopt(sys.argv[1:], "46A:f:p:Rv")
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
		elif (opt == "-f"):
			ffile = arg
		elif (opt == "-p"):
			port = arg
		elif (opt == "-R"):
			rand = True
		elif (opt == "-v"):
			verbose = True
	if (len(args) != 0):
		sys.stderr.write(USAGE % sys.argv[0])
		sys.exit(1)
	if (verbose):
		logger = logging.getLogger()
		logger.setLevel(logging.DEBUG)
	if (ffile):
		filelike = realfile(ffile)
	elif (rand):
		filelike = randomfile()
	else:
		filelike = Afile()
	poller = neubot.network.poller()
	connector(poller, family, address, port, filelike)
	poller.loop()
	sys.exit(0)

if (__name__ == "__main__"):
	main()
