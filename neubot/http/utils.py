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

import neubot
import ssl
import urlparse

def prettyprinter(write, direction, message, eol=""):
	stringio = message.serialize_headers()
	content = stringio.read()
	headers = content.split("\r\n")
	for line in headers:
		write(direction + line + eol)
		if (line == ""):
			break

def prettyprint(file, direction, message):			# Deprecated!
	prettyprinter(file.write, direction, message, eol="\n")

def urlsplit(uri):
	scheme, netloc, path, query, fragment = urlparse.urlsplit(uri)
	if (scheme != "http" and scheme != "https"):
		raise (neubot.error("Unknown scheme"))
	if (":" in netloc):
		address, port = netloc.split(":", 1)
	elif (scheme == "https"):
		address, port = netloc, "443"
	else:
		address, port = netloc, "80"
	if (not path):
		path = "/"
	pathquery = path
	if (query):
		pathquery = pathquery + "?" + query
	return (scheme, address, port, pathquery)

def response_unbounded(request, response):
	if (request.method != "HEAD"
	    and response["content-type"]
	    and not response["transfer-encoding"]
	    and not response["content-length"]):
		return (True)
	else:
		return (False)
