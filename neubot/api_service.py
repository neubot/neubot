# neubot/api_service.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
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

import StringIO
import urlparse
import cgi

from neubot.http.messages import Message
from neubot.notify import STATECHANGE
from neubot.net.poller import POLLER
from neubot.times import timestamp
from neubot.config import CONFIG
from neubot.notify import NOTIFIER
from neubot.state import STATE
from neubot.database import database
from neubot.marshal import unmarshal_objectx
from neubot.marshal import marshal_object

VERSION = "Neubot 0.3.6\n"


class ServiceHTTP(object):

    def serve(self, server, stream, request):
        path, query = urlparse.urlsplit(request.uri)[2:4]

        if path == "/api/config":
            self.api_config(stream, request)

        elif path == "/api/exit":
            self.api_exit(stream, request)

        elif path == "/api/speedtest":
            self.api_speedtest(stream, request, query)

        elif path == "/api/state":
            self.api_state(stream, request, query)

        elif path == "/api/version":
            self.api_version(stream, request)

        else:
            response = Message()
            response.compose(code="404", reason="Not Found",
                    body=StringIO.StringIO("404 Not Found"))
            stream.send_response(request, response)

    def api_config(self, stream, request):
        response = Message()

        if request.method == "POST":
            s = request.body.read()
            unmarshal_objectx(s, "application/x-www-form-urlencoded", CONFIG)
            STATE.update("config", CONFIG.__dict__)

        s = marshal_object(CONFIG, "application/json")
        stringio = StringIO.StringIO(s)
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype="application/json")
        stream.send_response(request, response)

    def api_speedtest(self, stream, request, query):
        since = 0
        until = timestamp()

        dictionary = cgi.parse_qs(query)
        if dictionary.has_key("since"):
            since = int(dictionary["since"][0])
            if since < 0:
                raise ValueError("Invalid query string")
        if dictionary.has_key("until"):
            until = int(dictionary["until"][0])
            if until < 0:
                raise ValueError("Invalid query string")

        response = Message()
        stringio = database.dbm.query_results_json(None, since, until, None)
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype="application/json")
        stream.send_response(request, response)

    def api_state(self, stream, request, query):
        dictionary = cgi.parse_qs(query)

        t = None
        if dictionary.has_key("t"):
            t = dictionary["t"][0]
            stale = NOTIFIER.needs_publish(STATECHANGE, t)
            if not stale:
                NOTIFIER.subscribe(STATECHANGE, self.api_state_complete,
                                   (stream, request, query, t))
                return

        self.api_state_complete(STATECHANGE, (stream, request, query, t))

    def api_state_complete(self, event, context):
        stream, request, query, t = context
        octets = STATE.marshal(t=t)
        stringio = StringIO.StringIO(octets)
        response = Message()
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype="application/json")
        stream.send_response(request, response)

    def api_version(self, stream, request):
        response = Message()
        stringio = StringIO.StringIO(VERSION)
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype="text/plain")
        stream.send_response(request, response)

    def api_exit(self, stream, request):
        POLLER.sched(1, POLLER.break_loop)
        response = Message()
        stringio = StringIO.StringIO("See you, space cowboy\n")
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype="text/plain")
        stream.send_response(request, response)
