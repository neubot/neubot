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
import cgi
import pprint
import re
import urlparse

from neubot.boot import VERSION
from neubot.compat import json
from neubot.config import ConfigError
from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.database import table_speedtest
from neubot.http.message import Message
from neubot.http.server import ServerHTTP
from neubot.log import LOG
from neubot.marshal import qs_to_dictionary
from neubot.net.poller import POLLER
from neubot.notify import NOTIFIER
from neubot.notify import STATECHANGE
from neubot.state import STATE

from neubot import privacy
from neubot import utils

CONFIG.register_defaults({
    "privacy.informed": False,
    "privacy.can_collect": False,
    "privacy.can_share": False,
})

CONFIG.register_descriptions({
    "privacy.informed": "You assert that you have read and understood the above privacy policy",
    "privacy.can_collect": "You give Neubot the permission to collect your Internet address",
    "privacy.can_share": "You give Neubot the permission to share your Internet address with the Internet community",
})


class ServerAPI(ServerHTTP):

    def __init__(self, poller):
        ServerHTTP.__init__(self, poller)
        self.dispatch = {
            "/api": self.api,
            "/api/": self.api,
            "/api/config": self.api_config,
            "/api/configlabels": self.api_configlabels,
            "/api/debug": self.api_debug,
            "/api/exit": self.api_exit,
            "/api/log": self.api_log,
            "/api/speedtest": self.api_speedtest,
            "/api/state": self.api_state,
            "/api/version": self.api_version,
        }

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
            reason = re.sub(r"[\x7f-\xff]", "", reason)
            LOG.exception(LOG.info)
            response = Message()
            response.compose(code="500", reason=reason,
                    body=StringIO.StringIO(reason))
            stream.send_response(request, response)

    def serve_request(self, stream, request):
        path, query = urlparse.urlsplit(request.uri)[2:4]
        if path in self.dispatch:
            self.dispatch[path](stream, request, query)
        else:
            response = Message()
            response.compose(code="404", reason="Not Found",
                    body=StringIO.StringIO("404 Not Found"))
            stream.send_response(request, response)

    def api(self, stream, request, query):
        response = Message()
        response.compose(code="200", reason="Ok", body=StringIO.StringIO(
          json.dumps(sorted(self.dispatch.keys()), indent=4)))
        stream.send_response(request, response)

    def api_config(self, stream, request, query):
        response = Message()

        indent, mimetype, sort_keys = None, "application/json", False
        dictionary = cgi.parse_qs(query)
        if "debug" in dictionary and utils.intify(dictionary["debug"][0]):
            indent, mimetype, sort_keys = 4, "text/plain", True

        if request.method == "POST":
            s = request.body.read()
            updates = qs_to_dictionary(s)
            privacy.check(updates)
            CONFIG.merge_api(updates, DATABASE.connection())
            STATE.update("config", updates)
            # Empty JSON b/c '204 No Content' is treated as an error
            s = "{}"
        else:
            s = json.dumps(CONFIG.conf, sort_keys=sort_keys, indent=indent)

        stringio = StringIO.StringIO(s)
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype=mimetype)
        stream.send_response(request, response)

    def api_configlabels(self, stream, request, query):

        indent, mimetype = None, "application/json"
        dictionary = cgi.parse_qs(query)
        if "debug" in dictionary and utils.intify(dictionary["debug"][0]):
            indent, mimetype = 4, "text/plain"

        response = Message()
        s = json.dumps(CONFIG.descriptions, sort_keys=True, indent=indent)
        stringio = StringIO.StringIO(s)
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype=mimetype)
        stream.send_response(request, response)

    def api_debug(self, stream, request, query):
        response = Message()
        debuginfo = {}
        NOTIFIER.snap(debuginfo)
        POLLER.snap(debuginfo)
        stringio = StringIO.StringIO()
        pprint.pprint(debuginfo, stringio)
        stringio.seek(0)
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype="text/plain")
        stream.send_response(request, response)

    def api_log(self, stream, request, query):

        response = Message()

        dictionary = cgi.parse_qs(query)
        if "debug" in dictionary and utils.intify(dictionary["debug"][0]):
            stringio = StringIO.StringIO()
            for ln in LOG.listify():
                ln = map(str, ln)
                stringio.write(" ".join(ln))
                stringio.write("\r\n")
            stringio.seek(0)
            mimetype = "text/plain"
        else:
            s = json.dumps(LOG.listify())
            stringio = StringIO.StringIO(s)
            mimetype = "application/json"

        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype=mimetype)
        stream.send_response(request, response)

    def api_speedtest(self, stream, request, query):
        since, until = -1, -1

        dictionary = cgi.parse_qs(query)
        if dictionary.has_key("since"):
            since = int(dictionary["since"][0])
        if dictionary.has_key("until"):
            until = int(dictionary["until"][0])

        indent, mimetype, sort_keys = None, "application/json", False
        dictionary = cgi.parse_qs(query)
        if "debug" in dictionary and utils.intify(dictionary["debug"][0]):
            indent, mimetype, sort_keys = 4, "text/plain", True

        response = Message()
        lst = table_speedtest.listify(DATABASE.connection(), since, until)
        s = json.dumps(lst, indent=indent, sort_keys=sort_keys)
        stringio = StringIO.StringIO(s)
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype=mimetype)
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

        indent, mimetype = None, "application/json"
        dictionary = cgi.parse_qs(query)
        if "debug" in dictionary and utils.intify(dictionary["debug"][0]):
            indent, mimetype = 4, "text/plain"

        dictionary = STATE.dictionarize(t=t)
        octets = json.dumps(dictionary, indent=indent)
        stringio = StringIO.StringIO(octets)
        response = Message()
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype=mimetype)
        stream.send_response(request, response)

    def api_version(self, stream, request, query):
        response = Message()
        stringio = StringIO.StringIO(VERSION)
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype="text/plain")
        stream.send_response(request, response)

    def api_exit(self, stream, request, query):
        POLLER.sched(0, POLLER.break_loop)
        response = Message()
        stringio = StringIO.StringIO("See you, space cowboy\n")
        response.compose(code="200", reason="Ok", body=stringio,
                         mimetype="text/plain")
        stream.send_response(request, response)