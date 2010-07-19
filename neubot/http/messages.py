# neubot/http/messages.py
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
import types

class message:
	def __init__(self, method="", uri="", code="", reason="", protocol=""):
		self.method = method
		self.uri = uri
		self.code = code
		self.reason = reason
		self.protocol = protocol
		self.headers = {}
		self.body = StringIO.StringIO("")
		self._proto = None
		self.scheme = ""
		self.address = ""
		self.port = ""
		self.pathquery = ""
		self.family = 0
		self.context = None
		if (self.method and self.code):
			raise (ValueError("Both method and code are set"))

	def serialize_headers(self):
		if (not self.method and not self.code):
			raise (Exception("Not initialized"))
		lst = []
		if (self.method):
			lst.append(self.method)
			lst.append(" ")
			if not self.uri.startswith("/"):
				if self.pathquery.startswith("/"):
					lst.append(self.pathquery)
				else:
					lst.append("/")
			else:
				lst.append(self.uri)
			lst.append(" ")
			lst.append(self.protocol)
		else:
			lst.append(self.protocol)
			lst.append(" ")
			lst.append(self.code)
			lst.append(" ")
			lst.append(self.reason)
		lst.append("\r\n")
		for key, value in self.headers.items():
			lst.append(key)
			lst.append(": ")
			lst.append(value)
			lst.append("\r\n")
		lst.append("\r\n")
		octets = "".join(lst)
		return (StringIO.StringIO(octets))

	def serialize_body(self):
		return (self.body)

	def __getitem__(self, key):
		if (type(key) != types.StringType):
			raise (TypeError("key should be a string"))
		key = key.lower()
		if (self.headers.has_key(key)):
			return (self.headers[key])
		return ("")

	def __setitem__(self, key, value):
		if (type(key) != types.StringType):
			raise (TypeError("key should be a string"))
		key = key.lower()
		if (self.headers.has_key(key)):
			value = self.headers[key] + ", " + value
		self.headers[key] = value

	def __delitem__(self, key):
		if (type(key) != types.StringType):
			raise (TypeError("key should be a string"))
		key = key.lower()
		if (self.headers.has_key(key)):
			del self.headers[key]
