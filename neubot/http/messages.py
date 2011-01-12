# neubot/http/messages.py

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
#
# This file is part of Neubot <http://www.neubot.org/>.
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
#

from neubot.utils import safe_seek
from StringIO import StringIO
from neubot.http.utils import date
from neubot.http.utils import urlsplit
from neubot.utils import fixkwargs
from os import SEEK_END, SEEK_SET
from socket import AF_INET, AF_UNSPEC
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

    def __del__(self):
        pass

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
# Note that compose() is meant for composing request messages
# from client-side and response messages from server-side.
# If the body is not present we explicitly set Content-Length at
# zero.  It costs nothing and the gain is that the browser does
# not guess that there is an unbounded response when we send a
# "200 Ok" response with no attached body.
#

COMPOSEARGS = {
    "address"    : "",
    "body"       : None,
    "code"       : "",
    "date"       : True,
    "family"     : AF_INET,
    "keepalive"  : True,
    "method"     : "",
    "mimetype"   : "",
    "nocache"    : True,
    "port"       : "",
    "pathquery"  : "",
    "protocol"   : "HTTP/1.1",
    "reason"     : "",
    "scheme"     : "",
    "uri"        : "",
}

def compose(m, **kwargs):
    fixkwargs(kwargs, COMPOSEARGS)
    m.method = kwargs["method"]
    if kwargs["uri"]:
        m.uri = kwargs["uri"]
        m.scheme, m.address, m.port, m.pathquery = urlsplit(m.uri)
        m["host"] = m.address + ":" + m.port
    else:
        m.scheme = kwargs["scheme"]
        m.address = kwargs["address"]
        m.port = kwargs["port"]
        m.pathquery = kwargs["pathquery"]
    m.code = kwargs["code"]
    m.reason = kwargs["reason"]
    m.protocol = kwargs["protocol"]
    if kwargs["nocache"]:
        if m.method:
            m["pragma"] = "no-cache"
        m["cache-control"] = "no-cache"
    if kwargs["date"]:
        m["date"] = date()
    if not kwargs["keepalive"]:
        m["connection"] = "close"
    if kwargs["body"]:
        m.body = kwargs["body"]
        safe_seek(m.body, 0, SEEK_END)
        length = m.body.tell()
        safe_seek(m.body, 0, SEEK_SET)
        m["content-length"] = str(length)
        if kwargs["mimetype"]:
            m["content-type"] = kwargs["mimetype"]
    else:
        m["content-length"] = "0"
    m.family = kwargs["family"]

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
