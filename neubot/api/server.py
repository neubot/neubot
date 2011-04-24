# neubot/api/server.py

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
import re

from neubot.compat import json
from neubot.config import ConfigError
from neubot.config import CONFIG
from neubot.database import database
from neubot.http.message import Message
from neubot.http.server import ServerHTTP
from neubot.log import LOG
from neubot.marshal import marshal_object
from neubot.marshal import qs_to_dictionary
from neubot.net.poller import POLLER
from neubot.notify import NOTIFIER
from neubot.notify import STATECHANGE
from neubot.state import STATE
from neubot.utils import timestamp

VERSION = "Neubot 0.3.6\n"

CONFIG.register_defaults({
    "privacy.informed": 0,
    "privacy.can_collect": 0,
    "privacy.can_share": 0,
})

CONFIG.register_descriptions({
    "privacy.informed": "You assert that you have read and understood the above privacy policy",
    "privacy.can_collect": "You give Neubot the permission to collect your Internet address",
    "privacy.can_share": "You give Neubot the permission to share your Internet address with the Internet community",
})


class ServerAPI(ServerHTTP):

    #
    # For local API services it make sense to disclose some
    # more information regarding the error that occurred while
    # in general it is not advisable to print the offending
    # exception.
    #
    def process_request(self, stream, request):
        try:
            self.serve_request(stream, request)
        except ConfigError, error:
            reason = re.sub(r"[\0-\31]", "", str(error))
            LOG.exception(LOG.info)
            response = Message()
            response.compose(code="500", reason=reason,
                    body=StringIO.StringIO(reason))
            stream.send_response(request, response)

    def serve_request(self, stream, request):
        path, query = urlparse.urlsplit(request.uri)[2:4]

        if path == "/api/config":
            self.api_config(stream, request)

        elif path == "/api/configlabels":
            self.api_configlabels(stream, request)

        elif path == "/api/exit":
            self.api_exit(stream, request)

        elif path == "/api/log":
            self.api_log(stream, request)

        elif path == "/api/speedtest":
            self.api_speedtest(stream, request, query)

        elif path == "/api/state":
            self.api_state(stream, request, query)

        elif path == "/api/testnow":
            self.api_testnow(stream, request, query)

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
            updates = qs_to_dictionary(s)
            CONFIG.merge_api(updates, database.connection())
            STATE.update("config", updates)
            # Empty JSON b/c '204 No Content' is treated as an error
            s = "{}"
        else:
            s = json.dumps(CONFIG.conf)

        stringio = StringIO.StringIO(s)
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype="application/json")
        stream.send_response(request, response)

    def api_configlabels(self, stream, request):
        response = Message()
        s = json.dumps(CONFIG.descriptions)
        stringio = StringIO.StringIO(s)
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype="application/json")
        stream.send_response(request, response)

    def api_log(self, stream, request):
        response = Message()
        s = json.dumps(LOG.serialize())
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
        stringio = database.dbm.query_results_json(since, until)
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

    def api_testnow(self, stream, request, query):
        dictionary = cgi.parse_qs(query)
        response = Message()

        if not "test" in dictionary:
            response.compose(code="500", reason="Missing test parameter",
              body=StringIO.StringIO("Missing test parameter"),
              mimetype="application/json")
            stream.send_response(request, response)
            return

        test = dictionary["test"][0]
        if test != "speedtest":
            response.compose(code="500", reason="No such test",
              body=StringIO.StringIO("No such test"),
              mimetype="application/json")
            stream.send_response(request, response)
            return

        #SPEEDTEST.start()
        response.compose(code="200", reason="Will run the test ASAP",
          body=StringIO.StringIO("Will run the test ASAP"),
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
