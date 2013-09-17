# neubot/dashtest/handler.py

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

""" The MPEG DASH request handler """

#
# Python3-ready: yes
#

from neubot import six

def receive(poller, message):
    """ Receive message on the dashtest/handler channel """
    poller.recv_message("dashtest/handler", receive)
    if (
        message.__class__.__name__ != "dict" or
        "stream" not in message or
        "method" not in message or
        "uri" not in message or
        "protocol" not in message or
        "headers" not in message or
        "body" not in message or
        "send_response" not in message
       ):
        return
    #
    # TODO Insert your code here
    #
    message["send_response"](
                             message,
                             "HTTP/1.1",
                             "200",
                             "Ok",
                             {
                              "Server": "neubot",
                              "Cache-Control": "no-cache",
                              "Content-Type": "text/plain",
                              "Content-Length": "8",
                             },
                             six.b("200 Ok\r\n")
                            )

def setup(poller):
    """ Recv on the dashtest/handler channel """
    poller.recv_message("dashtest/handler", receive)
