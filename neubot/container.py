# neubot/container.py
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
import logging
import socket

import neubot

MAXLENGTH = (1<<20)

class container:
    def __init__(self, poller, family=socket.AF_INET,
                 address="0.0.0.0", port="9773"):
        self.poller = poller
        neubot.http.acceptor(self, poller, address, port, family,
                             secure=False, certfile=None)
        self.funcs = {}

    def register(self, uri, func):
        self.funcs[uri] = func

    def aborted(self, acceptor):
        logging.error("Could not listen at '%s'" % acceptor)

    def listening(self, acceptor):
        logging.info("Listening at '%s'" % acceptor)

    def got_client(self, protocol):
        logging.info("[%s] Got client" % protocol)
        protocol.attach(self)

    def got_metadata(self, protocol):
        prefix = "[%s]   " % protocol
        logging.info("[%s] Pretty-printing request" % protocol)
        protocol.message.body = StringIO.StringIO()
        neubot.http.prettyprinter(logging.info, prefix, protocol.message)
        if protocol.message["transfer-encoding"] == "chunked":
            raise Exception("Unexpected chunked request")
        if protocol.message["content-length"]:
            length = int(protocol.message["content-length"])
            if length > MAXLENGTH:
                raise Exception("Body too large")

    def is_message_unbounded(self, protocol):
        return False

    def got_message(self, protocol):
        prefix = "[%s]   " % protocol
        if protocol.message["content-type"] == "application/json":
            protocol.message.body.seek(0)
            octets = protocol.message.body.read()
            neubot.utils.prettyprint_json(logging.info, prefix, octets)
        response = self._http_response(protocol="HTTP/1.1")
        try:
            func = self.funcs[protocol.message.uri]
            try:
                func(protocol, response)
            except Exception:
                neubot.utils.prettyprint_exception()
                response = self._http_response(protocol="HTTP/1.1",
                  code="500", reason="Internal Server Error")
        except KeyError:
            response = self._http_response(protocol="HTTP/1.1",
              code="404", reason="Not Found")
        logging.info("[%s] Pretty-printing response" % protocol)
        neubot.http.prettyprinter(logging.info, prefix, response)
        if response["content-type"] == "application/json":
            octets = response.body.read()
            neubot.utils.prettyprint_json(logging.info, prefix, octets)
            response.body.seek(0)
        logging.info("[%s] Sending response" % protocol.peername)
        protocol.sendmessage(response)

    def _http_response(self, protocol="", code="", reason=""):
        response = neubot.http.message()
        response.protocol = protocol
        response.code = code
        response.reason = reason
        response["date"] = neubot.http.date()
        response["cache-control"] = "no-cache"
        response["connection"] = "close"
        return response

    def message_sent(self, protocol):
        logging.info("[%s] Response sent" % protocol)
        logging.info("[%s] Waiting for client to close connection" % protocol)

    def closing(self, protocol):
        logging.info("[%s] The connection has been closed" % protocol)
