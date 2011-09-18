# neubot/negotiate.py

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

import collections
import hashlib
import random

from neubot.http.message import Message
from neubot.http.server import HTTP_SERVER
from neubot.http.server import ServerHTTP

from neubot.log import LOG
from neubot.compat import json

from neubot import utils

class NegotiatorModule(object):
    def unchoke(self, m):
        pass

    def collect(self, m):
        pass

class NegotiatorEOF(Exception):
    pass

class _Negotiator(object):

    def __init__(self):
        self._red = 32.0
        self._mods = {}
        self._parallel = 3

        #
        # We use three state variables: _queue is a FIFO
        # queue of streams representing clients that want
        # to perform a test; _known is set(_queue) and
        # is there to avoid scanning _queue each time we
        # receive a request from a stream; _delay is a
        # dictionary and is used to implement Comet: it
        # maps delayed streams with their state.
        #
        self._queue = collections.deque()
        self._known = set()
        self._delay = {}

    #
    # XXX For the queue length to be correct we need
    # to migrate the speedtest server to use this queue
    # otherwise the result does not account for that
    #
    def __len__(self):
        return len(self._queue)

    def register(self, name, mod):
        self._mods[name] = mod

    #
    # Allow to override the random number generator in
    # order to make it possible for code in regress/ to
    # test the behavior of this method.
    #
    def _random_early_discard(self, rnd=random.random):
        length = len(self._queue)
        threshold = (length - self._red) / self._red
        return rnd() < threshold

    def negotiate(self, m):

        # Fill in common response fields
        m["response_body"] = {
                              "real_address": m["stream"].peername[0],
                              "authorization": m["ident"],
                             }

        # Is the module registered?
        if not m["module"] in self._mods:
            raise KeyError(m["module"])

        # Do we already know the requesting stream?
        if not m["stream"] in self._known:

            discard = self._random_early_discard()
            if discard:
                raise NegotiatorEOF()

            else:
                # Keep track of this particular stream
                self._queue.append(m["stream"])
                self._known.add(m["stream"])

                # Make sure it will terminate and we'll notice that
                m["stream"].atclose(self._at_close)
                m["stream"].watchdog = 300
                m["stream"].created = utils.ticks()                     #XXX

                self._finalize_response(m, len(self._queue))
                self._send_response(m)

        #
        # We already know it... delay until something changes.
        # Note that we know something will change thanks to the
        # watchdog mechanism.
        #
        else:
            self._delay[m["stream"]] = m

    def collect(self, m):
        #
        # WARNING! Here it would be possible to prevent
        # choked streams to invoke collect() but still it
        # would not be possible from here to say whether
        # the test is complete.  So, to avoid creating
        # a false sense of security, we delegate the whole
        # decision of whether to accept the result or not
        # to the upstream module.  Period.
        #
        mod = self._mods[m["module"]]
        mod.collect(m)
        m["response_body"] = json.dumps(m["response_body"])

    def _at_close(self, stream, exception):

        # Remove all our references to stream
        self._queue.remove(stream)
        self._known.remove(stream)
        if stream in self._delay:
            del self._delay[stream]

        # Now update the queue and notify peers
        idx = -1
        for stream in self._queue:
            idx = idx + 1
            if not stream in self._delay:
                continue

            m = self._delay.pop(stream)
            self._finalize_response(m, idx)
            self._send_response(m)

    def _finalize_response(self, m, idx):
        # Tell upstream, if we have a new unchoke
        if idx < self._parallel:
            mod = self._mods[m["module"]]
            mod.unchoke(m)

        m["response_body"]["unchoked"] = idx < self._parallel
        m["response_body"]["queue_pos"] = idx
        m["response_body"] = json.dumps(m["response_body"])

    #
    # Here we expect errors, expecially when we are
    # running in the context of a closing stream and
    # we're sending delayed responses.
    #
    def _send_response(self, m):
        try:
            m["parent"].send_response(m)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            LOG.oops("send_response() failed: %s" % str(e))
            try:
                m["stream"].close()
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception, e:
                LOG.oops("close() failed: %s" % str(e))

NEGOTIATOR = _Negotiator()

def sha1stream(stream):
    return hashlib.sha1(str(stream)).hexdigest()

class _ServerNegotiate(ServerHTTP):

    def __init__(self, poller):
        ServerHTTP.__init__(self, poller)
        self.negotiator = NEGOTIATOR

    # Incoming body MUST BE bounded
    def got_request_headers(self, stream, request):
        return (request["transfer-encoding"] == "" and
          request.content_length() <= 1048576)

    def process_request(self, stream, request):
        m = {
            "code": "200",
            "ident": sha1stream(stream),
            "keepalive": True,
            "mimetype": "application/json",
            "reason": "Ok",
            "request_body": request.body.read(),
            "request": request,
            "response_body": "",
            "parent": self,
            "stream": stream,
        }

        # We expect a JSONized dictionary or nothing
        if m["request_body"]:
            if request["content-type"] != "application/json":
                raise RuntimeError("Invalid MIME type")
            m["request_body"] = dict(json.loads(m["request_body"]))
        else:
            m["request_body"] = {}

        if request.uri.startswith("/negotiate/"):
            m["module"] = request.uri.replace("/negotiate/", "")
            self.negotiator.negotiate(m)
            # NO because negotiate can use comet
            #self.send_response(m)

        elif request.uri.startswith("/collect/"):
            m["module"] = request.uri.replace("/collect/", "")
            self.negotiator.collect(m)
            self.send_response(m)

        else:
            m["code"] = "404"
            m["keepalive"] = False
            m["mimetype"] = "text/plain"
            m["reason"] = "Not Found"
            m["response_body"] = "Not Found"
            self.send_response(m)

    def send_response(self, m):
        response = Message()
        response.compose(code=m["code"], reason=m["reason"],
          keepalive=m["keepalive"], mimetype=m["mimetype"],
          body=m["response_body"])
        m["stream"].send_response(m["request"], response)
        if not m["keepalive"]:
            m["stream"].close()

def run(poller, conf):
    """ Start the client or server-side of the negotiate module """

    if not "negotiate.listen" in conf:
        LOG.oops("Thou shall pass 'negotiate.listen' to negotiate")

    _SERVER = _ServerNegotiate(None)
    HTTP_SERVER.register_child(_SERVER, "/negotiate/")
    HTTP_SERVER.register_child(_SERVER, "/collect/")
