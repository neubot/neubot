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

import neubot
from neubot.http.handlers import Receiver

TIMEOUT   = 300

class protocol(Receiver):
	def __init__(self, handler):
		self.handler = handler
		self.handler.attach(self)
		# delayed because we need to finish initialization first
		neubot.net.sched(0, self.handler.start_receiving)
		self.message = None
		self.application = None
		self.sockname = reduce(neubot.network.concatname,
		    handler.stream.myname)
		self.peername = reduce(neubot.network.concatname,
		    handler.stream.peername)
		self.begin = neubot.utils.ticks()
		neubot.net.register_periodic(self.periodic)
		self.have_body = True
		self.timeout = TIMEOUT

	def __str__(self):
		return self.peername

	def periodic(self, now):
		if now - self.begin > self.timeout:
			neubot.log.warning("Watchdog timeout")
			neubot.net.register_func(self.close)

	def passiveclose(self):
		self.handler.passiveclose()

	def oclosing(self):
		neubot.net.unregister_periodic(self.periodic)
		self.handler = None
                if self.application:
			self.application.closing(self)

	# ___ Begin neubot.http.Receiver impl. ___

	def closing(self):
		self.oclosing()

	def progress(self, data):
		self.got_data(data)

	def got_request_line(self, method, uri, protocol):
                self.message = neubot.http.message()
		self.message.method = method
		self.message.uri = uri
		self.message.protocol = protocol

	def got_response_line(self, protocol, code, reason):
                self.message = neubot.http.message()
		self.message.protocol = protocol
		self.message.code = code
		self.message.reason = reason

	def got_header(self, key, value):
		self.message[key] = value

	def end_of_headers(self):
		return self.got_metadata()

	def got_piece(self, piece):
		self.got_body_part(piece)

	def end_of_body(self):
		self.got_body()

	# ___ End neubot.http.Receiver impl. ___

	def got_body(self):
		if self.application:
			self.application.got_message(self)

	def got_body_part(self, octets):
		self.message.body.write(octets)

	def got_metadata(self):
		self.application.got_metadata(self)
		if self.have_body:
			if (self.message["transfer-encoding"] == "chunked"):
				return neubot.http.CHUNK_LENGTH, 0
			if (self.message["content-length"]):
				value = self.message["content-length"]
				try:
					length = int(value)
				except ValueError:
					length = -1
				if (length < 0):
					return neubot.http.ERROR, 0
				return neubot.http.BOUNDED, length
			if (self.application.is_message_unbounded(self)):
				return neubot.http.UNBOUNDED, 8000
		self.application.got_message(self)
		return neubot.http.IDLE, 0

	def sent_all(self):
		self.application.message_sent(self)

	def attach(self, application):
		self.application = application

	def close(self):
		self.handler.close()

	def sendmessage(self, msg):
            self.handler.bufferize(msg.serialize_headers())
            self.handler.bufferize(msg.serialize_body())
            self.handler.flush(self.sent_all, flush_progress=self.sent_data)

	def donthavebody(self):
		self.have_body = False

	def recvmessage(self):
		pass

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
