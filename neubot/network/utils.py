# neubot/network/utils.py
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

import errno
import logging
import logging.handlers
import os
import socket
import traceback

import neubot

def accept(sock, blocking=False):
	s, sa = sock.accept()
	s.setblocking(blocking)
	return (s)

def connect(family, address, port, blocking=False):
	logging.info("Connecting to '%s:%s'" % (address, port))
	lst = socket.getaddrinfo(address, port, family,
	    socket.SOCK_STREAM, 0, 0)
	for elem in lst:
		family, socktype, proto, canon, sa = elem
		try:
			repr = reduce(neubot.network.concatname, sa)
			logging.info("Trying with '%s'" % repr)
			s = socket.socket(family, socktype, proto)
			s.setblocking(blocking)
			err = s.connect_ex(sa)
			if (err != 0 and err != errno.EINPROGRESS
			    and err != errno.EWOULDBLOCK):
				raise (socket.error(err, os.strerror(err)))
			return (s)
		except socket.error:
			neubot.prettyprint_exception()
			s = None
	raise (neubot.error("can't connect to %s:%s" % (address, port)))

def listen(family, address, port, blocking=False):
	logging.info("Want to listen at '%s:%s'" % (address, port))
	lst = socket.getaddrinfo(address, port, family,
	    socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
	for elem in lst:
		family, socktype, proto, canon, sa = elem
		try:
			repr = reduce(neubot.network.concatname, sa)
			logging.info("Trying with '%s'" % repr)
			s = socket.socket(family, socktype, proto)
			s.setsockopt(socket.SOL_SOCKET,
			    socket.SO_REUSEADDR, 1)
			s.setblocking(blocking)
			s.bind(sa)
			s.listen(128)
			return (s)
		except socket.error:
			neubot.prettyprint_exception()
			s = None
	raise (neubot.error("can't listen at %s:%s" % (address, port)))
