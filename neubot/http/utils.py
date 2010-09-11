# neubot/http/utils.py
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

from neubot.http.handlers import BOUNDED
from neubot.http.handlers import CHUNK_LENGTH
from neubot.http.handlers import ERROR
from neubot.http.handlers import FIRSTLINE
from neubot.http.handlers import UNBOUNDED
from os.path import exists

import email.utils
import urlparse

def prettyprint(write, direction, msg, eol=""):
    stringio = msg.serialize_headers()
    content = stringio.read()
    headers = content.split("\r\n")
    for line in headers:
        write(direction + line + eol)
        if line == "":
            break

# compat
prettyprinter = prettyprint

def urlsplit(uri):
    scheme, netloc, path, query, fragment = urlparse.urlsplit(uri)
    if scheme != "http" and scheme != "https":
        raise Exception("Unknown scheme")
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

#
# response_unbounded() is less accurate than nextstate() and will
# be removed together with http.protocol
#

def response_unbounded(request, response):
    if (request.method != "HEAD"
     and response["content-type"]
     and not response["transfer-encoding"]
     and not response["content-length"]):
        return True
    else:
        return False

def date():
    return email.utils.formatdate(usegmt=True)

#
# Functions to negotiate MIME type
#

def _parse_accept(accept):
    if accept == "":
        return [(1.0, "*/*")]
    result = []
    pass1 = accept.split(",")
    for entry in pass1:
        pass2 = entry.split(";")
        if len(pass2) == 2:
            mimetype = pass2[0]
            quality = float(pass2[1].replace("q=", ""))
        elif len(pass2) == 1:
            mimetype = pass2[0]
            quality = 1.0
        else:
            continue
        result.append((quality, mimetype))
    return sorted(result, reverse=True)

def _select_mime(accept, available):
    ret = None
    for quality, mimetype in accept:
        if mimetype in available:
            ret = mimetype
            break
    return ret

def negotiate_mime(m, available, default):
    accept = _parse_accept(m["accept"])
    mimetype = _select_mime(accept, available)
    if mimetype == None:
        mimetype = default
    return mimetype

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

def _make_filename(uri, default):
    scheme, address, port, pathquery = urlsplit(uri)
    ret = default
    index = pathquery.rfind("/")
    if index >= 0:
        ret = pathquery[index+1:]
        if not ret:
            ret = default
    return ret

def make_filename(uri, default):
    filename = _make_filename(uri, default)
    index = 0
    temp = filename
    while exists(temp):
        if index == 100:
            raise ValueError("Can't generate unique filename")
        temp = filename + "." + str(index)
        index = index + 1
    filename = temp
    return filename

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
