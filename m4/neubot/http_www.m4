# @DEST@

#
# Copyright (c) 2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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

""" HTTP WWW server """

include(`m4/include/aaa_base.m4')

NEUBOT_PY3_READY()

import email.utils
import logging
import mimetypes
import os.path
import sys
import xml.sax.saxutils

from neubot.http_server import HTTPServer
from neubot.http_server import HTTPSServer

from neubot import six
from neubot import utils_path

dnl
dnl HTTP_METHOD_IS(<stream>, <method>)
dnl
define(`HTTP_METHOD_IS', ``$1.http_request_method == six.b($2)'')

dnl
dnl HTTP_METHOD_IS_NOT(<stream>, <method>)
dnl
define(`HTTP_METHOD_IS_NOT', ``$1.http_request_method != six.b($2)'')

changequote([, ])
HTML_EXTRA_ENTITIES = [{'"': "&quot;", "'": "&apos;"}]
changequote(`, ')

dnl
dnl HTTP_HTMLENTITIES(<string>)
dnl
define(`HTTP_HTMLENTITIES',
    xml.sax.saxutils.escape($1, HTML_EXTRA_ENTITIES)
)

dnl
dnl HTTP_SEND_ERROR(<stream>, <code>, <reason>)
dnl
define(`HTTP_SEND_ERROR',
            `string = "%s %s" % ($2, $3)
        string = HTTP_HTMLENTITIES(string)dnl

        body = []
        body.append("<!DOCTYPE html>\r\n")
        body.append("<HTML>\r\n")
        body.append("  <HEAD>\r\n")
        body.append("    <TITLE>%s</TITLE>\r\n" % string)
        body.append("  </HEAD>\r\n")
        body.append("  <BODY>\r\n")
        body.append("    <H1>%s</H1>\r\n" % string)
        body.append("  </BODY>\r\n")
        body.append("</HTML>\r\n")
        body = "".join(body)
        body = body.encode("UTF-8")

        headers = {
            "Allow": "GET, HEAD",
            "Date": email.utils.formatdate(usegmt=True),
            "Server": "NEUBOT_PRODUCT()",
            "Content-Length": str(len(body)),
            "Content-Type": "text/html; charset=UTF-8",
        }

        $1.http_append_response("HTTP/1.1", $2,
          $3, headers, body)
        $1.buff_obuff_flush()
        $1.http_read_headers()
')

dnl
dnl HTTP_CHECK_HOST_HEADER_IF_NEEDED(<stream>)
dnl
define(`HTTP_CHECK_HOST_HEADER_IF_NEEDED',
        `if (
            $1.http_request_protocol == six.b("HTTP/1.1") and
            not $1.http_request_headers.get(six.b("host"))
           ):
            logging.warning("http: The host header is missing")
            self._http_send_error("403", "Forbidden")
            return
')

dnl
dnl HTTP_FAIL_IF_INVALID_ROOTDIR(<stream>)
dnl
define(`HTTP_FAIL_IF_INVALID_ROOTDIR',
        `if not os.path.isdir(self.rootdir):
            logging.warning("http: the root directory is invalid")
            self._http_send_error("403", "Forbidden")
            return
')

dnl
dnl HTTP_REJECT_FULL_URIs(<stream>)
dnl
define(`HTTP_REJECT_FULL_URIs',
        `if not $1.http_request_uri.startswith(six.b("/")):
            logging.warning("http: the request_uri is not an absolute path")
            self._http_send_error("403", "Forbidden")
            return
')

dnl
dnl HTTP_GET_NORMPATH(<stream>, <normpath>, <rootdir>)
dnl
define(`HTTP_GET_NORMPATH',
        `try:
            parsed = six.urlparse.urlsplit($1.http_request_uri)
            $2 = parsed[2].decode("ASCII")
            logging.debug("http: the original URL path is: %s", $2)
            $2 = six.urllib.unquote($2)
            logging.debug("http: the unquoted URL path is: %s", $2)
            $2 = utils_path.append($3, $2)
            if not $2:
                raise RuntimeError("cannot append path to rootdir")
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            NEUBOT_ERRNO(error)
            NEUBOT_PERROR(warning, http: cannot normalize path, error)
            self._http_send_error("404", "Not Found")
            return
')

dnl
dnl HTTP_READFILE(<stream>, <body>, <normpath>)
dnl
define(`HTTP_READFILE',
        `try:
            filep = open($3, "rb")
            $2 = filep.read()
            filep.close()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            NEUBOT_ERRNO(error)
            NEUBOT_PERROR(warning, http: failed to open file, error)
            self._http_send_error("404", "Not Found")
            return
')

dnl
dnl HTTP_COMPUTE_TYPE(<stream>, <type>, <encoding>, <normpath>)
dnl
define(`HTTP_COMPUTE_TYPE',
        `try:
            $2, $3 = mimetypes.guess_type($4)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            NEUBOT_ERRNO(error)
            NEUBOT_PERROR(warning, http: failed to compute size, error)
            self._http_send_error("500", "Internal Server Error")
            return
')

dnl
dnl HTTP_FILL_RESPONSE(<stream>, <code>, <reason>, <content-length>,
dnl   <content-type>, <content-encoding>)
dnl
define(`HTTP_FILL_RESPONSE',
        `headers = {
            "Allow": "GET, HEAD",
            "Date": email.utils.formatdate(usegmt=True),
            "Server": "NEUBOT_PRODUCT()",
            "Content-Length": str($4),
            "Content-Type": $5,
        }
        if $6:
            headers["Content-Encoding"] = $6
        if not headers["Content-Type"]:
            headers["Content-Type"] = "text/plain; charset=UTF-8"
        $1.http_append_response("HTTP/1.1", $2, $3, headers, None)
')

dnl
dnl HTTP_LISTDIR(<stream>, <normpath>, <indent>)
dnl
define(`HTTP_LISTDIR',
        `basedir = $2.replace(self.rootdir, "", 1)
$3        basedir = HTTP_HTMLENTITIES(basedir)dnl

$3        body = []
$3        body.append("<!DOCTYPE html>\r\n")
$3        body.append("<HTML>\r\n")
$3        body.append("  <HEAD>\r\n")
$3        body.append("    <TITLE>Content of %s/</TITLE>\r\n" % basedir)
$3        body.append("  </HEAD>\r\n")
$3        body.append("  <BODY>\r\n")
$3        body.append("    <H1>Content of %s/</H1>\r\n" % basedir)
$3        if basedir:
$3            body.append("    <A HREF=\"%s/..\">../</A><BR>\r\n" % (basedir))

$3        for name in sorted(os.listdir($2)):
$3            if name.startswith("."):
$3                continue

$3            fullpath = os.sep.join([$2, name])
$3            if os.path.isdir(fullpath):
$3                isdir = "/"
$3            elif os.path.isfile(fullpath):
$3                isdir = ""
$3            else:
$3                continue

$3            srvrpath = os.sep.join([basedir, name])
$3            name = HTTP_HTMLENTITIES(name)dnl
$3            srvrpath = HTTP_HTMLENTITIES(srvrpath)dnl

$3            body.append("    <A HREF=\"%s\">%s%s</A><BR>\r\n" % (
$3                        srvrpath, name, isdir))

$3        body.append("  </BODY>\r\n")
$3        body.append("</HTML>\r\n")
$3        body = "".join(body)
$3        body = body.encode("UTF-8")

$3        headers = {
$3            "Allow": "GET, HEAD",
$3            "Date": email.utils.formatdate(usegmt=True),
$3            "Server": "NEUBOT_PRODUCT()",
$3            "Content-Length": str(len(body)),
$3            "Content-Type": "text/html; charset=UTF-8",
$3        }

$3        $1.http_append_response("HTTP/1.1", "200", "Ok", headers, body)
$3        $1.buff_obuff_flush()
$3        $1.http_read_headers()
')

dnl
dnl HTTP_WWW_SERVER_IMPL()
dnl
define(`HTTP_WWW_SERVER_IMPL',
    `def _http_send_error(self, code, reason):
        """ Send an HTTP error response """
        HTTP_SEND_ERROR(self, code, reason)

    def _http_listdir(self, normpath):
        """ Lists the content of the selected directory """
        HTTP_LISTDIR(self, normpath)

    def http_handle_headers(self, error):
        if error:
            self.sock_close()
            return
        self.http_read_body()

    def http_handle_body(self, error):
        if error:
            self.sock_close()
            return

        HTTP_CHECK_HOST_HEADER_IF_NEEDED(self)
        HTTP_FAIL_IF_INVALID_ROOTDIR(self, self.rootdir)
        if (
            HTTP_METHOD_IS_NOT(self, "GET") and
            HTTP_METHOD_IS_NOT(self, "HEAD")
           ):
            logging.warning("http: method not implemented")
            self._http_send_error("501", "Not Implemented")
            return

        HTTP_REJECT_FULL_URIs(self)
        normpath = None
        HTTP_GET_NORMPATH(self, normpath, self.rootdir)
        if os.path.isdir(normpath):
            self._http_listdir(normpath)
            return

        body = None
        HTTP_READFILE(self, body, normpath)
        content_type = None
        encoding = None
        HTTP_COMPUTE_TYPE(self, content_type, encoding, normpath)
        content_length = len(body)

        HTTP_FILL_RESPONSE(self, "200", "Ok", content_length,
                                 content_type, encoding)dnl
        if HTTP_METHOD_IS(self, "GET"):
            self.http_append_data(body)

        self.buff_obuff_flush()
        self.http_read_headers()

    def tcp_accept_complete(self, error, stream):
        self.tcp_wait_accept()
        if error:
            return

        stream.rootdir = self.rootdir

        dnl
        dnl Insert code to complete the class here
        dnl

')

class HTTPWWWServer(HTTPServer):
    """ HTTP WWW server """

    def __init__(self, poller):
        HTTPServer.__init__(self, poller)
        self.rootdir = None

    HTTP_WWW_SERVER_IMPL()dnl
        stream.http_read_headers()

class HTTPSWWWServer(HTTPSServer):
    """ HTTPS WWW server """

    def __init__(self, poller):
        HTTPSServer.__init__(self, poller)
        self.certfile = None
        self.rootdir = None

    HTTP_WWW_SERVER_IMPL()dnl
        stream.ssl_handshake(True, self.certfile)

    def ssl_handshake_complete(self, error):
        if error:
            self.sock_close()
            return
        self.http_read_headers()
