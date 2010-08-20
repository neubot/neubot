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

from StringIO import StringIO
from socket import AF_UNSPEC
from types import StringType

class Message:
    def __init__(self, method="", uri="", code="", reason="", protocol=""):
        self.method = method
        self.uri = uri
        self.code = code
        self.reason = reason
        self.protocol = protocol
        self.headers = {}
        self.body = StringIO("")
        self.scheme = ""
        self.address = ""
        self.port = ""
        self.pathquery = ""
        self.family = AF_UNSPEC
        if self.method and self.code:
            raise ValueError("Both method and code are set")

    #
    # The client code saves the whole uri in self.uri and then
    # splits the URI in pieces and, after that, self.pathquery
    # contains path+query.  The server code, instead, saves in
    # self.uri the URI and does not split it.  So we must con-
    # sider both self.pathquery and self.uri, and we must give
    # precedence to self.pathquery--or we will send requests
    # that some web servers do not accept.
    #

    def serialize_headers(self):
        if not self.method and not self.code:
            raise Exception("Not initialized")
        lst = []
        if self.method:
            lst.append(self.method)
            lst.append(" ")
            if self.pathquery:
                lst.append(self.pathquery)
            elif self.uri:
                lst.append(self.uri)
            else:
                lst.append("/")
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
        return StringIO(octets)

    def serialize_body(self):
        return self.body

    def __getitem__(self, key):
        if type(key) != StringType:
            raise TypeError("key should be a string")
        key = key.lower()
        if self.headers.has_key(key):
            return self.headers[key]
        return ""

    def __setitem__(self, key, value):
        if type(key) != StringType:
            raise TypeError("key should be a string")
        key = key.lower()
        if self.headers.has_key(key):
            value = self.headers[key] + ", " + value
        self.headers[key] = value

    def __delitem__(self, key):
        if type(key) != StringType:
            raise TypeError("key should be a string")
        key = key.lower()
        if self.headers.has_key(key):
            del self.headers[key]

#
# For compatibility with existing code
#

class Messagexxx(Message):
    def __init__(self, method="", uri="", code="", reason="", protocol=""):
        Message.__init__(self, method, uri, code, reason, protocol)
        self._proto = None
        self.context = None

message = Messagexxx

__all__ = [ "message" ]
