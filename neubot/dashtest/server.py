# neubot/dashtest/server.py

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

from neubot.dashtest.http_server import HTTPServer

class DASHServer(HTTPServer):
    """ The MPEG DASH server """

    def __init__(self, poller):
        HTTPServer.__init__(self, poller)

    def tcp_accept_complete(self, error, stream):
        self.tcp_wait_accept()
        if error:
            return
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
        #
        # Note: we pass the function to send the response in
        # the message, therefore the handler code can work on
        # top of different HTTP implementations.
        #
        message = {
                   "stream": self,
                   "method": self.http_request_method,
                   "uri": self.http_request_uri,
                   "protocol": self.http_request_protocol,
                   "headers": self.http_request_headers,
                   "body": self.http_request_body,
                   "send_response": self._send_response,
                  }
        self.sock_poller.send_message("dashtest/handler", message)

    @staticmethod
    def _send_response(orig_message, protocol, code, reason,
                       headers, body):
        """ Send the response back to the client """
        stream = orig_message["stream"]
        del orig_message
        stream.http_append_response(protocol, code, reason, headers, body)
        stream.buff_obuff_flush()

    def buff_flush_complete(self, error):
        if error:
            self.sock_close()
            return

def receive(poller, message):
    """ Receive a message on the dashtest/server channel """
    poller.recv_message("dashtest/server", receive)
    if (
        message.__class__.__name__ != "dict" or
        "address" not in message or
        "port" not in message or
        "family" not in message
       ):
        return
    try:
        server = DASHServer(poller)
        server.sock_bind(message["family"], message["address"],
                         message["port"])
        server.tcp_listen(10)
        server.tcp_wait_accept()
    except (KeyboardInterrupt, SystemExit):
        raise

def setup(poller):
    """ Recv on the dashtest/server channel """
    poller.recv_message("dashtest/server", receive)
