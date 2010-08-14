# neubot/http/protocols.py
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
import collections
import logging
import os

import neubot

SMALLMESSAGE = 64000

PROTOCOLS = [ "HTTP/1.1", "HTTP/1.0" ]
TIMEOUT   = 300

class protocol:
	def __init__(self, adaptor):
		self.adaptor = adaptor
		self.adaptor.attach(self)
		self.message = None
		self.application = None
		self.sockname = reduce(neubot.network.concatname,
		    adaptor.connection.myname)
		self.peername = reduce(neubot.network.concatname,
		    adaptor.connection.peername)
		self.begin = neubot.utils.ticks()
		self.poller = self.adaptor.connection.poller
		self.poller.register_periodic(self.periodic)
		self.have_body = True
		self.timeout = TIMEOUT
		self.waitingclose = False

	def __str__(self):
		return self.peername

	def periodic(self, now):
		if now - self.begin > self.timeout:
			logging.warning("Watchdog timeout")
			self.poller.register_func(self.close)

        #
        # In passive close mode we wait for the client to close the
        # connection, and, if this does not happen for one second,
        # we close the connection.  We read a message because we want
        # the poller to check the socket for readability--indeed the
        # socket becomes readable when the other end closes the conn-
        # ection.
        # XXX Do not lower the timeout to one second because that caused
        # measurements to fail when running from an home connection such
        # as my home ADSL.
        #

	def passiveclose(self):
		#self.timeout = 1
		self.waitingclose = True
		self.recvmessage()

	def closing(self):
		self.poller.unregister_periodic(self.periodic)
		self.adaptor = None
                if self.application:
			self.application.closing(self)

	def got_body(self):
		if self.application:
			self.application.got_message(self)

	def got_body_part(self, octets):
		self.message.body.write(octets)

	def got_metadata(self, metadata):
		if self.waitingclose:
		    logging.warning("Client should have closed the connection")
		    return
		self.message = neubot.http.message()
		headers = metadata.split("\r\n")
		for line in headers:
			if (line == ""):
				break
			if (not self.message.protocol):
				vector = line.split(" ", 2)
				if (len(vector) != 3):
					raise (Exception("Invalid line"))
				if (vector[0] in PROTOCOLS):
					self.message.protocol = vector[0]
					self.message.code = vector[1]
					self.message.reason = vector[2]
				elif (vector[2] in PROTOCOLS):
					self.message.method = vector[0]
					self.message.uri = vector[1]
					self.message.protocol = vector[2]
				else:
					raise (Exception("Invalid line"))
			else:
				vector = line.split(":", 1)		# XXX
				if (len(vector) != 2):
					raise (Exception("Invalid line"))
				key, value = vector
				key, value = key.strip(), value.strip()
				self.message[key] = value
		self.application.got_metadata(self)
		if self.have_body:
			if (self.message["transfer-encoding"] == "chunked"):
				self.adaptor.get_chunked_body()
				return
			if (self.message["content-length"]):
				value = self.message["content-length"]
				try:
					length = int(value)
				except ValueError:
					length = -1
				if (length < 0):
					raise (Exception("Invalid line"))
				self.adaptor.get_bounded_body(length)
				return
			if (self.application.is_message_unbounded(self)):
				self.adaptor.get_unbounded_body()
				return
		self.application.got_message(self)

	def sent_all(self):
		self.application.message_sent(self)

	def attach(self, application):
		self.application = application

	def close(self):
		self.adaptor.close()

	def sendmessage(self, msg):
            queue = collections.deque()
            queue.append(msg.serialize_headers())
            queue.append(msg.serialize_body())
            length = 0
            for stringio in queue:
                stringio.seek(0, os.SEEK_END)
                length += stringio.tell()
                stringio.seek(0, os.SEEK_SET)
            if length <= SMALLMESSAGE:
                vector = []
                while len(queue) > 0:
                    stringio = queue.popleft()
                    vector.append(stringio.read())
                content = "".join(vector)
                stringio = StringIO.StringIO(content)
                queue.append(stringio)
            for stringio in queue:
                self.adaptor.send(stringio)

	def donthavebody(self):
		self.have_body = False

	def recvmessage(self):
		self.adaptor.get_metadata()

	def __del__(self):
		pass

	#
	# XXX Here we surround got_data() and sent_data() because some
	# pieces of code define these two functions (like api.py) and
	# others don't.  This is the simplest solution in the short run.
	#

	def got_data(self, octets):
		try:
			self.application.got_data(self, octets)
		except AttributeError:
			pass

	def sent_data(self, octets):
		try:
			self.application.sent_data(self, octets)
		except AttributeError:
			pass
