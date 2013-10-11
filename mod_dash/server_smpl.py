# mod_dash/server_smpl.py

#
# Copyright (c) 2013 Antonio Servetti <antonio.servetti@polito.it>
#
# Copyright (c) 2010-2013
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

""" MPEG DASH server """

# Adapted from neubot/speedtest/server.py

from neubot.http.message import Message
from neubot.http.server import ServerHTTP

#
# The default body size is small enough that the body, and
# the related HTTP headers, should fit into a single 1500
# bytes Ethernet packet.
#
DASH_DEFAULT_BODY_SIZE = 1000

#
# XXX We don't serve bodies larger than this size. To serve
# larger bodies we need to adopt an iterator approach.
#
DASH_MAXIMUM_BODY_SIZE = 104857600

DASH_MAXIMUM_REPETITIONS = 60

class DASHServerSideState(object):
    """ Per stream server-side state """
    def __init__(self):
        self.count = 0

class DASHServerSmpl(ServerHTTP):
    """ Server-side of the MPEG DASH test """

    def got_request_headers(self, stream, request):
        """ Filter incoming HTTP requests """
        # Adapted from neubot/negotiate/server.py

        #
        # NOTE Ignore the request body.  First of all, we are
        # not interested in reading it, we just want to receive
        # it.  Moreover, reading it leads to framentation, as
        # we need to actually allocate and then free all those
        # bytes.  (This is true especially when testing with
        # fast Neubot clients.)  This fix brings the amount of
        # memory consumed by the server under control again.
        #
        request.body.write = lambda data: None

        if not stream.opaque:
            stream.opaque = DASHServerSideState()

        stream.set_timeout(10)

        return request.uri.startswith("/dash/download")

    def process_request(self, stream, request):
        """ Process the incoming HTTP request """

        if request.uri.startswith("/dash/download"):

            context = stream.opaque
            context.count += 1
            if context.count > DASH_MAXIMUM_REPETITIONS:
                raise RuntimeError("dash: too many repetitions")

            #
            # Parse the "/dash/download/<size>" optional RESTful
            # parameter of the request.
            #
            # If such parameter is not parseable into an integer,
            # we let the error propagate, i.e., the poller will
            # automatically close the stream socket.
            #
            body_size = DASH_DEFAULT_BODY_SIZE
            resource_size = request.uri.replace("/dash/download", "")
            if resource_size.startswith("/"):
                resource_size = resource_size[1:]
            if resource_size:
                body_size = int(resource_size)

            if body_size < 0:
                raise RuntimeError("dash: negative body size")
            if body_size > DASH_MAXIMUM_BODY_SIZE:
                body_size = DASH_MAXIMUM_BODY_SIZE

            #
            # XXX We don't have a quick solution for generating
            # and sending many random bytes from Python.
            #
            # Or, better, we have a couple of ideas, but they
            # have not been implemented into Neubot yet.
            #
            pattern = request["Authorization"]
            if not pattern:
                pattern = "deadbeef"
            body = pattern * ((body_size / len(pattern)) + 1)
            if len(body) > body_size:
                body = body[:body_size]

            response = Message()
            response.compose(code="200", reason="Ok", body=body,
                             mimetype="video/mp4")

            stream.set_timeout(15)

            stream.send_response(request, response)

        else:
            # For robustness
            raise RuntimeError("dash: unexpected URI")
