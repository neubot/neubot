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

import email.utils
import urlparse

def prettyprinter(write, direction, msg, eol=""):
    stringio = msg.serialize_headers()
    content = stringio.read()
    headers = content.split("\r\n")
    for line in headers:
        write(direction + line + eol)
        if line == "":
            break

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

def parse_accept(accept):
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

def select_mime(accept, available):
    for quality, mimetype in accept:
        if mimetype in available:
            return mimetype
    return None

def negotiate_mime(m, available, default):
    accept = parse_accept(m["accept"])
    mimetype = select_mime(accept, available)
    if mimetype == None:
        mimetype = default
    return mimetype
