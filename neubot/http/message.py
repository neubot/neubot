# neubot/http/message.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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

''' An HTTP message '''

# Will be replaced by neubot/http_utils.py

import StringIO
import email.utils
import collections
import urlparse
import socket
import os
import logging

from neubot.log import oops

from neubot import compat
from neubot import utils
from neubot import utils_net

REDIRECT = '''\
<HTML>
 <HEAD>
  <TITLE>Found</TITLE>
 </HEAD>
 <BODY>
  You should go to <A HREF="%s">%s</A>.
 </BODY>
</HTML>
'''

def urlsplit(uri):
    ''' Wrapper for urlparse.urlsplit() '''
    scheme, netloc, path, query, fragment = urlparse.urlsplit(uri)
    if scheme != "http" and scheme != "https":
        raise ValueError("Unknown scheme")

    # Unquote IPv6 [<address>]:<port> or [<address>]
    if netloc.startswith('['):
        netloc = netloc[1:]
        index = netloc.find(']')
        if index == -1:
            raise ValueError("Invalid quoted IPv6 address")
        address = netloc[:index]

        port = netloc[index + 1:].strip()
        if not port:
            if scheme == 'https':
                port = "443"
            else:
                port = "80"
        elif not port.startswith(':'):
            raise ValueError("Missing port separator")
        else:
            port = port[1:]

    elif ":" in netloc:
        address, port = netloc.split(":", 1)
    elif scheme == "https":
        address, port = netloc, "443"
    else:
        address, port = netloc, "80"

    if not path:
        path = "/"
    pathquery = path
    if query:
        pathquery = pathquery + "?" + query
    return scheme, address, port, pathquery

class Message(object):

    ''' Represents an HTTP message '''

    def __init__(self, method="", uri="", code="", reason="", protocol=""):
        ''' Initialize the HTTP message '''
        self.method = method
        self.uri = uri
        self.scheme = ""
        self.address = ""
        self.port = ""
        self.pathquery = ""
        self.code = code
        self.reason = reason
        self.protocol = protocol

        # For server-side accounting
        self.requestline = " ".join((method, uri, protocol))

        self.headers = collections.defaultdict(str)
        self.body = StringIO.StringIO("")

        self.family = socket.AF_UNSPEC
        self.response = None
        self.length = 0

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
        ''' Serialize message headers '''
        vector = []

        if self.method:
            vector.append(self.method)
            vector.append(" ")
            if self.pathquery:
                vector.append(self.pathquery)
            elif self.uri:
                vector.append(self.uri)
            else:
                vector.append("/")
            vector.append(" ")
            vector.append(self.protocol)

        else:
            vector.append(self.protocol)
            vector.append(" ")
            vector.append(self.code)
            vector.append(" ")
            vector.append(self.reason)

        logging.debug("> %s", "".join(vector))
        vector.append("\r\n")

        for key, value in self.headers.items():
            key = "-".join(map(lambda s: s.capitalize(), key.split("-")))
            vector.append(key)
            vector.append(": ")
            vector.append(value)

            logging.debug("> %s: %s", key, value)
            vector.append("\r\n")

        logging.debug(">")
        vector.append("\r\n")

        string = "".join(vector)
        string = utils.stringify(string)
        return StringIO.StringIO(string)

    def serialize_body(self):
        ''' Serialize message body '''
        self.prettyprintbody(">")
        return self.body

    #
    # RFC2616 section 4.2 says that "Each header field consists
    # of a name followed by a colon (":") and the field value. Field
    # names are case-insensitive."  So, for simplicity, we use all-
    # lowercase header names but we capitalize header names, as most
    # applications do, before sending them on the wire.
    #
    def __getitem__(self, key):
        ''' Return an header '''
        return self.headers[key.lower()]

    def __setitem__(self, key, value):
        ''' Save an header '''
        key = key.lower()
        if self.headers.has_key(key):
            value = self.headers[key] + ", " + value
        self.headers[key] = value

    def __delitem__(self, key):
        ''' Delete an header '''
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
    def compose(self, **kwargs):
        ''' Prepare a request on the client side '''
        self.method = kwargs.get("method", "")

        if kwargs.get("uri", ""):
            self.uri = kwargs.get("uri", "")
            (self.scheme, self.address,
             self.port, self.pathquery) = urlsplit(self.uri)
            self["host"] = self.address + ":" + self.port
        else:
            self.scheme = kwargs.get("scheme", "")
            self.address = kwargs.get("address", "")
            self.port = kwargs.get("port", "")
            self.pathquery = kwargs.get("pathquery", "")
            if self.method:
                #
                # "A client MUST include a Host header field in all HTTP/1.1
                # request messages.  If the requested URI does not include
                # an Internet host name for the service being requested, then
                # the Host header field MUST be given with an empty value."
                #               -- RFC 2616
                #
                self["host"] = kwargs.get("host", "")
                if not self["host"]:
                    oops("Missing host header")

        self.code = kwargs.get("code", "")
        self.reason = kwargs.get("reason", "")
        self.protocol = kwargs.get("protocol", "HTTP/1.1")

        if kwargs.get("nocache", True):
            if self.method:
                self["pragma"] = "no-cache"
            self["cache-control"] = "no-cache"

        if kwargs.get("date", True):
            self["date"] = email.utils.formatdate(usegmt=True)

        if not kwargs.get("keepalive", True):
            self["connection"] = "close"

        #
        # Curl(1) does not enter into up_to_eof mode unless a
        # content-type is specified, for this reason I've added
        # an OOPS below.
        # TODO Looking again at RFC2616 after adding this bits
        # realized that another patch is due to make the code
        # that deals with body and length better.
        #
        if kwargs.get("up_to_eof", False):
            if not "mimetype" in kwargs:
                oops("up_to_eof without mimetype")
            self["content-type"] = kwargs.get("mimetype",
                                       "text/plain")

        elif kwargs.get("body", None):
            self.body = kwargs.get("body", None)
            if isinstance(self.body, basestring):
                self.length = len(self.body)
            else:
                utils.safe_seek(self.body, 0, os.SEEK_END)
                self.length = self.body.tell()
                utils.safe_seek(self.body, 0, os.SEEK_SET)
            self["content-length"] = str(self.length)
            if kwargs.get("mimetype", ""):
                self["content-type"] = kwargs.get("mimetype", "")

        elif kwargs.get("chunked", None):
            self.body = kwargs.get("chunked", None)
            self.length = -1
            self["transfer-encoding"] = "chunked"
            if kwargs.get("mimetype", ""):
                self["content-type"] = kwargs.get("mimetype", "")

        else:
            self["content-length"] = "0"

        self.family = kwargs.get("family", socket.AF_INET)

    def compose_redirect(self, stream, target):
        ''' Prepare a redirect response '''
        if not target.startswith("/"):
            target = "/" + target
        location = "http://%s%s" % (utils_net.format_epnt(
                                    stream.myname), target)
        body = REDIRECT % (target, target)
        self.compose(code="302", reason="Found", body=body,
                     mimetype="text/html; charset=UTF-8")
        self["location"] = location

    def prettyprintbody(self, prefix):
        ''' Pretty print body '''

        return  # Slow in some cases; disable

        if self["content-type"] not in ("application/json", "text/xml",
                                        "application/xml"):
            return

        # Grab the whole body
        if not isinstance(self.body, basestring):
            body = self.body.read()
        else:
            body = self.body

        # Decode the body
        if self["content-type"] == "application/json":
            string = compat.json.dumps(compat.json.loads(body),
              indent=4, sort_keys=True)
        elif self["content-type"] in ("text/xml", "application/xml"):
            string = body

        # Prettyprint
        for line in string.split("\n"):
            logging.debug("%s %s", prefix, line.rstrip())

        # Seek to the beginning if needed
        if not isinstance(self.body, basestring):
            utils.safe_seek(self.body, 0)

    def content_length(self):
        ''' Get content length '''
        string = self["content-length"]
        length = int(string)
        if length < 0:
            raise ValueError("Content-Length must be positive")
        return length
