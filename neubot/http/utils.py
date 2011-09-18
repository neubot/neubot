# neubot/http/utils.py

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

import email.utils
import urlparse

from neubot.http.stream import BOUNDED
from neubot.http.stream import CHUNK_LENGTH
from neubot.http.stream import ERROR
from neubot.http.stream import FIRSTLINE
from neubot.http.stream import UNBOUNDED
from neubot.log import LOG
from neubot import utils
from neubot import compat

def urlsplit(uri):
    scheme, netloc, path, query, fragment = urlparse.urlsplit(uri)
    if scheme != "http" and scheme != "https":
        raise ValueError("Unknown scheme")
    if ":" in netloc:
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

def date():
    return email.utils.formatdate(usegmt=True)

#
# Quoting from RFC2616, sect. 4.3:
#
#   "The presence of a message-body in a request is signaled by the
#    inclusion of a Content-Length or Transfer-Encoding header field
#    in the request's message-headers. [...] A server SHOULD read and
#    forward a message-body on any request; if the request method does
#    not include defined semantics for an entity-body, then the message
#    -body SHOULD be ignored when handling the request."
#
#   "[...] All responses to the HEAD request method MUST NOT include a
#    message-body, even though the presence of entity-header fields might
#    lead one to believe they do. All 1xx (informational), 204 (no content),
#    and 304 (not modified) responses MUST NOT include a message-body.  All
#    other responses do include a message-body, although it MAY be of zero
#    length."
#

def _parselength(message):
    value = message["content-length"]
    try:
        length = int(value)
    except ValueError:
        return ERROR, 0
    else:
        if length < 0:
            return ERROR, 0
        elif length == 0:
            return FIRSTLINE, 0
        else:
            return BOUNDED, length

def nextstate(request, response=None):
    if response == None:
        if request["transfer-encoding"] == "chunked":
            return CHUNK_LENGTH, 0
        elif request["content-length"]:
            return _parselength(request)
        else:
            return FIRSTLINE, 0
    else:
        if (request.method == "HEAD" or response.code[0] == "1" or
         response.code == "204" or response.code == "304"):
            return FIRSTLINE, 0
        elif response["transfer-encoding"] == "chunked":
            return CHUNK_LENGTH, 0
        elif response["content-length"]:
            return _parselength(response)
        else:
            # make sure the server *will* close the connection
            if response.protocol == "HTTP/1.0":
                return UNBOUNDED, 8000
            elif response["connection"] == "close":
                return UNBOUNDED, 8000
            else:
                return FIRSTLINE, 0

#
# Parse 'range:' header
# Here we don't care of Exceptions as long as these exceptions
# are ValueErrors, because the caller expects this function to
# succed OR to raise ValueError.
#

def parse_range(message):
    vector = message["range"].replace("bytes=", "").strip().split("-")
    first, last = map(int, vector)
    if first < 0 or last < 0 or last < first:
        raise ValueError("Cannot parse range header")
    return first, last

#
# Content-Length
#

def content_length(m):
    s = m["content-length"]
    ln = int(s)
    if ln < 0:
        raise ValueError("Content-Length must be positive")
    return ln
