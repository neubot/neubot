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

""" HTTP proxy """

include(`m4/include/aaa_base.m4')

NEUBOT_PY3_READY()

import logging
import socket

from neubot.http_client import HTTPClient
from neubot.http_server import HTTPServer
from neubot.network_core import BuffStreamSocket

from neubot import six

HTTP_PROXY_MAXRECV = (1 << 20)

HTTP_PROXY_MAXLINELENGTH = 512

HTTP_PROXY_MAXHEADERS = 32

class HTTPProxyClient(HTTPClient):
    """ HTTP proxy client """

    def __init__(self, poller):
        HTTPClient.__init__(self, poller)
        self.body = None
        self.headers = None
        self.method = None
        self.path = None
        self.parent = None

    def proxy_connect(self, parent, method, uri, headers, body):
        """ Connect to URI and send the specified request """

        self.parent = parent

        self.method = method.decode("UTF-8")

        uri = uri.decode("UTF-8")
        splitted = six.urlparse.urlsplit(uri)

        netloc = splitted[1]
        if ":" in netloc:
            hostname, port = netloc.split(":", 1)
        else:
            hostname, port = netloc, 80
        port = int(port)

        self.path = splitted[2]
        if splitted[3]:
            self.path += "?"
            self.path += splitted[3]
        if splitted[4]:
            self.path += "#"
            self.path += splitted[4]

        self.headers = {}
        for name, value in headers.items():
            if name in (six.b("proxy-connection")):
                continue
            name = name.decode("ASCII").title()
            value = value.decode("ASCII")
            self.headers[name] = value
        self.headers["Connection"] = "close"

        self.body = six.b("").join(body)

        if not self.headers.get("Host"):
            self.headers["Host"] = hostname

        if self.headers.get("Transfer-Encoding") == "chunked":
            del self.headers["Transfer-Encoding"]

        self.headers["Content-Length"] = str(len(self.body))

        error = self.sock_connect(socket.AF_INET, socket.SOCK_STREAM,
                                  hostname, port)
        if error:
            return error

        self.tcp_wait_connected()

    def tcp_connect_complete(self, error):
        if error:
            self.parent.proxy_complete(self, error)
            return
        self.http_append_request(self.method, self.path, "HTTP/1.1",
                                 self.headers, None)
        self.http_append_data(self.body)
        self.buff_obuff_flush()

    def buff_flush_complete(self, error):
        if error:
            self.parent.proxy_complete(self, error)
            return
        self.http_read_headers()

    def http_handle_headers(self, error):
        if error:
            self.parent.proxy_complete(self, error)
            return
        self.http_read_body()

    def http_handle_body(self, error):
        self.parent.proxy_complete(self, error)

    def sock_handle_close(self, error):
        HTTPClient.sock_handle_close(self, error)
        logging.debug("proxy: sock_handle_close(): %s", self)
        self.parent = None

class HTTPProxyServer(HTTPServer):
    """ HTTP proxy server """

    def __init__(self, poller):
        HTTPServer.__init__(self, poller)
        self.client = None

    def tcp_accept_complete(self, error, stream):
        self.tcp_wait_accept()
        if not error:
            stream.http_read_headers()

    def http_handle_headers(self, error):
        if error:
            self.sock_close()
            return
        self.http_read_body()

    def http_handle_body(self, error):
        if error:
            self.sock_close()
            return

        client = HTTPProxyClient(self.sock_poller)
        error = client.proxy_connect(
                                     self,
                                     self.http_request_method,
                                     self.http_request_uri,
                                     self.http_request_headers,
                                     self.http_request_body,
                                    )

        if error:
            self.sock_close()
            return

    def proxy_complete(self, client, error):
        """ The proxy client connected to the remote host """
        if error:
            self.sock_close()
            client.sock_close()
            return

        code = client.http_response_code.decode("UTF-8")
        reason = client.http_response_reason.decode("UTF-8")

        headers = {}
        for name, value in client.http_response_headers.items():
            if name in (six.b("connection")):
                continue
            name = name.decode("ASCII").title()
            value = value.decode("ASCII")
            headers[name] = value
        headers["Proxy-Connection"] = "close"

        body = six.b("").join(client.http_response_body)

        if headers.get("Transfer-Encoding") == "chunked":
            del headers["Transfer-Encoding"]

        headers["Content-Length"] = str(len(body))

        client.sock_close()

        self.http_append_response("HTTP/1.1", code, reason, headers, None)
        self.http_append_data(body)
        self.buff_obuff_flush()

        self.http_read_headers()

    def buff_flush_complete(self, error):
        if error:
            self.sock_close()

    def sock_handle_close(self, error):
        HTTPServer.sock_handle_close(self, error)
        logging.debug("proxy: sock_handle_close(): %s", self)
        self.client = None

class HTTPConnectProxyClient(BuffStreamSocket):
    """ Client for the HTTP CONNECT proxy """

    def __init__(self, poller):
        BuffStreamSocket.__init__(self, poller)
        self.proxy_parent = None

    def tcp_connect_complete(self, error):
        self.proxy_parent.proxy_connect_complete(self, error)

    def sock_recv_complete(self, error, data):
        if error or not data:
            self.proxy_parent.sock_close()
            return
        self.proxy_parent.proxy_handle_data(data)
        self.sock_recv(HTTP_PROXY_MAXRECV)

    def proxy_handle_data(self, data):
        """ We have data to send downstream """
        ###logging.debug(">>> %d bytes", len(data))
        self.buff_obuff_append(data)
        self.buff_obuff_flush()

    def buff_flush_complete(self, error):
        if error:
            self.proxy_parent.sock_close()

    def sock_handle_close(self, error):
        BuffStreamSocket.sock_handle_close(self, error)
        logging.debug("proxy: sock_handle_close(): %s", self)
        self.proxy_parent = None

class HTTPConnectProxy(BuffStreamSocket):
    """ CONNECT proxy for relying HTTPS """

    def __init__(self, poller):
        BuffStreamSocket.__init__(self, poller)
        self.proxy_address = None
        self.proxy_client = None
        self.proxy_line_count = 0
        self.proxy_port = None

    def tcp_accept_complete(self, error, stream):
        self.tcp_wait_accept()
        if not error:
            stream.sock_recv(HTTP_PROXY_MAXRECV)

    def sock_recv_complete(self, error, data):

        if error:
            self.sock_close()
            return
        if not data:
            self.sock_close()
            return

        if self.proxy_client:

            # XXX Would be better to add ibuff a function to extract all
            if self.buff_ibuff:
                for buff_data in self.buff_ibuff:
                    if buff_data:
                        self.proxy_client.proxy_handle_data(buff_data)
                self.buff_ibuff = []
                self.buff_ibuff_count = 0

            self.proxy_client.proxy_handle_data(data)

            self.sock_recv(HTTP_PROXY_MAXRECV)
            return

        self.buff_ibuff_append(data)

        while True:
            line, count = self.buff_ibuff_readline(True)
            if not line:
                if count > HTTP_PROXY_MAXLINELENGTH:
                    logging.warning("proxy: line too long")
                    self.sock_close()
                    return
                self.sock_recv(HTTP_PROXY_MAXRECV)
                return

            line = line.rstrip()
            logging.debug("< %s", line)

            self.proxy_line_count += 1

            if self.proxy_line_count > HTTP_PROXY_MAXHEADERS:
                logging.warning("proxy: too many headers")
                self.sock_close()
                return

            if not line:
                break
            if self.proxy_line_count > 1:
                continue

            vector = line.split(None, 3)
            if (
                   len(vector) != 3
                or vector[0] != six.b("CONNECT")
                or six.b(":") not in vector[1]
                or not vector[2].startswith(six.b("HTTP/"))
                or vector[2][5:] not in (six.b("1.0"), six.b("1.1"))
               ):
                logging.warning("proxy: invalid CONNECT line")
                self.sock_close()
                return
            address, port = vector[1].split(six.b(":"), 1)
            self.proxy_address = address
            try:
                self.proxy_port = int(port)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.warning("proxy: invalid port number")
                self.sock_close()
                return
            if self.proxy_port < 1 or self.proxy_port > 65535:
                logging.warning("proxy: invalid port number")
                self.sock_close()
                return

        if not self.proxy_address or not self.proxy_port:
            logging.warning("proxy: no CONNECT information available")
            self.sock_close()
            return

        client = HTTPConnectProxyClient(self.sock_poller)
        client.sock_connect(socket.AF_INET, socket.SOCK_STREAM,
                            self.proxy_address, self.proxy_port)
        client.proxy_parent = self
        client.tcp_wait_connected()

    def proxy_connect_complete(self, client, error):
        """ The connect() we started above is now complete """

        self.proxy_client = client

        if error:
            self.sock_close()
            return

        logging.debug("> HTTP/1.0 200 Ok")
        logging.debug("> ")

        self.buff_obuff_append(six.b("HTTP/1.0 200 OK\r\n\r\n"))
        self.buff_obuff_flush()

        logging.debug("proxy: tunnel established")

        self.proxy_client.sock_recv(HTTP_PROXY_MAXRECV)
        self.sock_recv(HTTP_PROXY_MAXRECV)

    def proxy_handle_data(self, data):
        """ We have data to send upstream """
        ###logging.debug("<<< %d bytes", len(data))
        self.buff_obuff_append(data)
        self.buff_obuff_flush()

    def buff_flush_complete(self, error):
        if error:
            self.sock_close()

    def sock_handle_close(self, error):
        BuffStreamSocket.sock_handle_close(self, error)
        logging.debug("proxy: sock_handle_close(): %s", self)
        if self.proxy_client:
            self.proxy_client.sock_close()
            self.proxy_client = None
