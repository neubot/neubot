# neubot/dashtest/client.py

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

""" The MPEG DASH client """

#
# Python3-ready: yes
#

import logging

from neubot.dashtest.http_client import HTTPClient

class DASHClient(HTTPClient):
    """ The MPEG DASH client """

    def __init__(self, poller):
        HTTPClient.__init__(self, poller)
        self.address = None
        self.authorization = None
        self.family = None
        self.host = None
        self.port = None
        self.reply_to = None

    def sock_connect(self, family, address, port):
        self.family = family
        self.address = address
        self.port = port
        HTTPClient.sock_connect(self, family, address, port)

    def tcp_connect_complete(self, error):
        if error:
            self.sock_poller.send_message(self.reply_to, {})
            self.sock_close()
            return
        #
        # TODO Add your code here
        #
        headers = {
                   "Authorization": self.authorization,
                   "Host": self.host,
                   "Cache-Control": "no-cache",
                   "Pragma": "no-cache",
                   "User-Agent": "neubot",
                  }
        self.http_append_request("GET", "/", "HTTP/1.1", headers, None)
        self.buff_obuff_flush()

    def buff_flush_complete(self, error):
        if error:
            self.sock_poller.send_message(self.reply_to, {})
            self.sock_close()
            return
        self.http_read_headers()

    def http_handle_headers(self, error):
        if error:
            self.sock_poller.send_message(self.reply_to, {})
            self.sock_close()
            return
        self.http_read_body()

    def http_handle_body(self, error):
        if error:
            self.sock_poller.send_message(self.reply_to, {})
            self.sock_close()
            return
        #
        # TODO Add your code here
        #
        message = {
                   "authorization": self.authorization,
                   "reply_to": self.reply_to,
                   "address": self.address,
                   "port": self.port,
                   "family": self.family,
                   "host": self.host,
                  }
        self.sock_poller.send_message("dashtest/collector", message)
        self.sock_close()

def receive(poller, message):
    """ Receive message on the dashtest/client channel """
    poller.recv_message("dashtest/client", receive)
    if (
        message.__class__.__name__ != "dict" or
        "authorization" not in message or
        "reply_to" not in message or
        "address" not in message or
        "port" not in message or
        "family" not in message or
        "host" not in message
       ):
        return
    try:
        client = DASHClient(poller)
        client.authorization = message["authorization"]
        client.reply_to = message["reply_to"]
        client.host = message["host"]
        client.sock_connect(message["family"], message["address"],
                            message["port"])
        client.tcp_wait_connected()
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        logging.warning("dashtest: unhandled exception", exc_info=1)
        poller.send_message(message["reply_to"], {})

def setup(poller):
    """ Recv on the dashtest/client channel """
    poller.recv_message("dashtest/client", receive)
