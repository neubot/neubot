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

''' Implements API server '''

import cgi
import gc
import pprint
import re
import urllib
import urlparse
import logging
import sys

from neubot.main.common import VERSION
from neubot.compat import json
from neubot.config import ConfigError
from neubot.debug import objgraph
from neubot.http.message import Message
from neubot.http.server import ServerHTTP
from neubot.net.poller import POLLER
from neubot.notify import NOTIFIER
from neubot.state import STATECHANGE
from neubot.speedtest.client import QUEUE_HISTORY
from neubot.state import STATE

from neubot import config_api
from neubot import privacy
from neubot import log_api
from neubot import runner_api
from neubot import utils
from neubot import api_data
from neubot import api_results
from neubot import utils_hier

from neubot.utils_api import NotImplementedTest

class ServerAPI(ServerHTTP):

    ''' Server for API '''

    def __init__(self, poller):
        ServerHTTP.__init__(self, poller)
        self._dispatch = {
            "/api": self._api,
            "/api/": self._api,
            "/api/data": api_data.api_data,
            "/api/config": config_api.config_api,
            "/api/debug": self._api_debug,
            "/api/index": self._api_index,
            "/api/exit": self._api_exit,
            "/api/log": log_api.log_api,
            "/api/results": api_results.api_results,
            "/api/runner": runner_api.runner_api,
            "/api/state": self._api_state,
            "/api/version": self._api_version,
        }

    #
    # Update the stream timestamp each time we receive a new
    # request.  Which means that the watchdog timeout will
    # reclaim inactive streams only.
    # For local API services it make sense to disclose some
    # more information regarding the error that occurred while
    # in general it is not advisable to print the offending
    # exception.
    #
    def process_request(self, stream, request):
        ''' Process incoming request '''
        stream.created = utils.ticks()
        try:
            self._serve_request(stream, request)
        except (ConfigError, NotImplementedTest):
            error = sys.exc_info()[1]
            reason = re.sub(r"[\0-\31]", "", str(error))
            reason = re.sub(r"[\x7f-\xff]", "", reason)
            logging.info('Internal error while serving response', exc_info=1)
            response = Message()
            response.compose(code="500", reason=reason,
                    body=reason)
            stream.send_response(request, response)

    def _serve_request(self, stream, request):
        ''' Serve incoming request '''
        request_uri = urllib.unquote(request.uri)
        path, query = urlparse.urlsplit(request_uri)[2:4]
        if path in self._dispatch:
            self._dispatch[path](stream, request, query)
        else:
            response = Message()
            response.compose(code="404", reason="Not Found",
                    body="404 Not Found")
            stream.send_response(request, response)

    def _api(self, stream, request, query):
        ''' Implements /api URI '''
        response = Message()
        response.compose(code="200", reason="Ok",
          body=json.dumps(sorted(self._dispatch.keys()), indent=4))
        stream.send_response(request, response)

    @staticmethod
    def _api_debug(stream, request, query):
        ''' Implements /api/debug URI '''
        response = Message()
        debuginfo = {}
        NOTIFIER.snap(debuginfo)
        POLLER.snap(debuginfo)
        debuginfo["queue_history"] = QUEUE_HISTORY
        debuginfo["WWWDIR"] = utils_hier.WWWDIR
        gc.collect()
        debuginfo['typestats'] = objgraph.typestats()
        body = pprint.pformat(debuginfo)
        response.compose(code="200", reason="Ok", body=body,
                         mimetype="text/plain")
        stream.send_response(request, response)

    @staticmethod
    def _api_index(stream, request, query):
        '''
         Redirect either to /index.html or /privacy.html depending on
         whether the user has already set privacy permissions or not
        '''
        response = Message()
        if not privacy.allowed_to_run():
            response.compose_redirect(stream, '/privacy.html')
        else:
            response.compose_redirect(stream, '/index.html')
        stream.send_response(request, response)

    def _api_state(self, stream, request, query):
        ''' Implements /api/state URI '''
        dictionary = cgi.parse_qs(query)

        otime = None
        if "t" in dictionary:
            otime = dictionary["t"][0]
            stale = NOTIFIER.needs_publish(STATECHANGE, otime)
            if not stale:
                NOTIFIER.subscribe(STATECHANGE, self._api_state_complete,
                                   (stream, request, query, otime), True)
                return

        self._api_state_complete(STATECHANGE, (stream, request, query, otime))

    @staticmethod
    def _api_state_complete(event, context):
        ''' Callback invoked when the /api/state has changed '''
        stream, request, query, otime = context

        indent, mimetype = None, "application/json"
        dictionary = cgi.parse_qs(query)
        if "debug" in dictionary and utils.intify(dictionary["debug"][0]):
            indent, mimetype = 4, "text/plain"

        dictionary = STATE.dictionarize()
        octets = json.dumps(dictionary, indent=indent)
        response = Message()
        response.compose(code="200", reason="Ok", body=octets,
                         mimetype=mimetype)
        stream.send_response(request, response)

    @staticmethod
    def _api_version(stream, request, query):
        ''' Implements /api/version URI '''
        response = Message()
        response.compose(code="200", reason="Ok", body=VERSION,
                         mimetype="text/plain")
        stream.send_response(request, response)

    @staticmethod
    def _api_exit(stream, request, query):
        ''' Implements /api/exit URI '''
        # This is the expedite way of breaking out of poller loop
        raise KeyboardInterrupt('api_server: received /api/exit request')
