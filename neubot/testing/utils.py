# neubot/testing/utils.py
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
import fcntl
import os

import neubot

class stdio_connection:
	def __init__(self, poller, fd):
		self.poller = poller
		self.fd = fd
		flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
		flags |= os.O_NONBLOCK
		fcntl.fcntl(self.fd, fcntl.F_SETFL, flags)
		self.protocol = None

	def readable(self):
		self.protocol.readable()

	def writable(self):
		self.protocol.writable()

	def closing(self):
		self.protocol.closing()

	def fileno(self):
		return (self.fd)

	def attach(self, protocol):
		self.protocol = protocol

	def send(self, buf):
		try:
			return (os.write(self.fd, buf))
		except os.error, (code, reason):
			if (code == errno.EWOULDBLOCK or
			    code == errno.EPIPE):
				return (0)
			else:
				raise (neubot.error(code, reason))

	def recv(self, cnt):
		try:
			buf = os.read(self.fd, cnt)
			if (buf == ""):
				raise (neubot.error(errno.EPIPE, "Broken pipe"))
			return (buf)
		except os.error, (code, reason):
			if (code == errno.EWOULDBLOCK or
			    code == errno.EPIPE):
				return ("")
			else:
				raise (neubot.error(code, reason))

	def set_readable(self):
		self.poller.set_readable(self)

	def set_writable(self):
		self.poller.set_writable(self)

	def unset_readable(self):
		self.poller.unset_readable(self)

	def unset_writable(self):
		self.poller.unset_writable(self)

	def close(self):
		self.poller.close(self)
