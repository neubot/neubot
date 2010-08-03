# neubot/http/acceptors.py
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

import neubot
import socket

class acceptor:
	def __init__(self, application, poller, address, port,
	    family=socket.AF_INET, secure=False, certfile=None):
		self.application = application
		self.poller = poller
		self.address = address
		self.port = port
		self.family = family
		self.secure = secure
		self.certfile = certfile
		neubot.net.listen(self.address, self.port, self._accepted,
		    cantbind=self._failed, poller=self.poller,
                    family=self.family, secure=self.secure,
		    certfile=self.certfile)

	def __str__(self):
		return self.address + ":" + self.port

	def _failed(self):
		self.application.aborted(self)

	def _accepted(self, connection):
		adaptor = neubot.http.adaptor(connection)
		protocol = neubot.http.protocol(adaptor)
		self.application.got_client(protocol)
