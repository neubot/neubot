# neubot/dashtest/negotiate_client.py

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

""" Negotiate client for the DASH test """

#
# Python3-ready: yes
#

import logging

from neubot.dashtest.http_client import HTTPClient

# External dependencies: not so good for a plugin!
from neubot.compat import json
from neubot.state import STATE

from neubot import utils_version
from neubot import six

class DASHNegotiator(HTTPClient):
    """ Negotiates a DASH test """

    def __init__(self, poller):
        HTTPClient.__init__(self, poller)
        self.address = None
        self.authorization = None
        self.family = None
        self.reply_to = None
        self.host = None

    def sock_connect(self, family, address, port):

        STATE.update("test_latency", "---", publish=False)
        STATE.update("test_download", "---", publish=False)
        STATE.update("test_upload", "---", publish=False)
        STATE.update("test_name", "dashtest", publish=False)
        STATE.update("negotiate")

        self.address = address
        self.family = family

        HTTPClient.sock_connect(self, family, address, port)

    def tcp_connect_complete(self, error):
        if error:
            self.sock_poller.send_message(self.reply_to, {})
            self.sock_close()
            return
        self._do_negotiate()

    def _do_negotiate(self):
        """ Start the negotiation """
        logging.debug("dashtest: negotiate in progress...")
        negotiate_request = {}
        body = six.b(json.dumps(negotiate_request))
        headers = {
                   "Host": self.host,
                   "User-Agent": utils_version.HTTP_HEADER,
                   "Content-Type": "application/json",
                   "Content-Length": str(len(body)),
                   "Cache-Control": "no-cache",
                   "Pragma": "no-cache",
                   "Authorization": self.authorization,
                  }
        self.http_append_request("GET", "/negotiate/dashtest", "HTTP/1.1",
                                 headers, body)
        self.buff_obuff_flush()
        self.http_read_headers()

    def http_handle_headers(self, error):
        if error:
            self.sock_poller.send_message(self.reply_to, {})
            self.sock_close()
            return
        if self.http_response_code != six.b("200"):
            self.sock_poller.send_message(self.reply_to, {})
            self.sock_close()
            return
        tmp = self.http_response_headers[six.b("content-type")]
        if tmp != six.b("application/json"):
            self.sock_poller.send_message(self.reply_to, {})
            self.sock_close()
            return
        self.http_read_body()

    def http_handle_body(self, error):
        if error:
            self.sock_poller.send_message(self.reply_to, {})
            self.sock_close()
            return
        try:
            negotiate_response = json.loads(six.b("").join(
              self.http_response_body))
        except (KeyboardInterrupt, SystemExit):
            raise
        else:
            self.sock_poller.send_message(self.reply_to, {})
            self.sock_close()
            return

        #
        # The response from the server MUST be a dictionary and MUST
        # contain at least the following fields:
        #
        # authorization: authorization information
        # port: port to connect to
        # queue_pos: current position in queue
        # unchoked: whether the client can run the test now or not
        #

        if (
            negotiate_response.__class__.__name__ != "dict" or
            "authorization" not in negotiate_response or
            "port" not in negotiate_response or
            "queue_post" not in negotiate_response or
            "unchoked" not in negotiate_response
           ):
            self.sock_poller.send_message(self.reply_to, {})
            self.sock_close()
            return

        self.authorization = negotiate_response["authorization"]

        if not negotiate_response["unchoked"]:
            queue_pos = negotiate_response["queue_pos"]
            logging.debug("dashtest: negotiate complete... in queue (%d)",
                          queue_pos)
            STATE.update("negotiate", {"queue_pos": queue_pos})
            self.sock_poller.sched(self._do_negotiate)
            return

        logging.debug("dashtest: negotiate complete... unchoked")
        message = {
                   "reply_to": self.reply_to,
                   "address": self.address,
                   "port": negotiate_response["port"],
                   "family": self.family,
                   "host": self.host,
                   "authorization": self.authorization,
                  }
        self.sock_poller.send_message("dashtest/client", message)
        self.sock_close()

def negotiator_receive(poller, message):
    """ Receive message on the dashtest/negotiator channel """
    poller.recv_message("dashtest/negotiator", negotiator_receive)
    if (
        message.__class__.__name__ != "dict" or
        "reply_to" not in message or
        "address" not in message or
        "port" not in message or
        "family" not in message or
        "host" not in message
       ):
        return
    try:
        negotiator = DASHNegotiator(poller)
        negotiator.reply_to = message["reply_to"]
        negotiator.host = message["host"]
        negotiator.sock_connect(message["family"], message["address"],
                                message["port"])
        negotiator.tcp_wait_connected()
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        poller.send_message(message["reply_to"], {})
