# neubot/negotiate/server.py

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

''' Negotiate server '''

import collections
import random
import logging

from neubot.config import CONFIG
from neubot.http.message import Message
from neubot.http.server import ServerHTTP
from neubot.compat import json

class NegotiateServerModule(object):

    ''' Each test should implement this interface '''

    # The minimal collect echoes the request body
    def collect(self, stream, request_body):
        ''' Invoked at the end of the test, to collect data '''
        return request_body

    # Only speedtest reimplements this method
    def collect_legacy(self, stream, request_body, request):
        ''' Legacy interface to collect that also receives the
            request object: speedtest needs to inspect the Authorization
            header when the connecting client is pretty old '''
        return self.collect(stream, request_body)

    # The minimal unchoke returns the stream unique identifier only
    def unchoke(self, stream, request_body):
        ''' Invoked when a stream is authorized to take the test '''
        return { 'authorization': str(hash(stream)) }

class NegotiateServer(ServerHTTP):

    ''' Common code layer for /negotiate and /collect '''

    def __init__(self, poller):
        ''' Initialize the negotiator '''
        ServerHTTP.__init__(self, poller)
        self.queue = collections.deque()
        self.modules = {}
        self.known = set()

    def register_module(self, name, module):
        ''' Register a module '''
        self.modules[name] = module

    #
    # Protect the server from requests with huge request bodies
    # and filter-out unhandled URIs.
    # The HTTP layer should close() the stream when we return
    # False here.
    #
    def got_request_headers(self, stream, request):
        ''' Decide whether we can accept this HTTP request '''
        isgood = (request['transfer-encoding'] == '' and
                  request.content_length() <= 1048576 and
                  (request.uri.startswith('/negotiate/') or
                   request.uri.startswith('/collect/')))
        return isgood

    def process_request(self, stream, request):
        ''' Process a /collect or /negotiate HTTP request '''

        #
        # Here we are liberal and we process a GET request plus body
        # as it was a POST or PUT request, however we warn because the
        # body has no meaning when you send a GET request.
        #
        if request.method != "POST" and request.method != "PUT":
            logging.warning("%s: GET plus body is surprising", request.uri)

        #
        # We always pass upstream the collect request.  If it is
        # not authorized the module does not have the identifier in
        # its global table and will raise a KeyError.
        # Here we always keepalive=False so the HTTP layer closes
        # the connection and we are notified that the queue should
        # be changed.
        #
        if request.uri.startswith('/collect/'):
            module = request.uri.replace('/collect/', '')
            module = self.modules[module]
            request_body = json.load(request.body)

            response_body = module.collect_legacy(stream, request_body, request)
            response_body = json.dumps(response_body)

            response = Message()
            response.compose(code='200', reason='Ok', body=response_body,
                             keepalive=False, mimetype='application/json')
            stream.send_response(request, response)

        #
        # The first time we see a stream, we decide whether to
        # accept or drop it, depending on the length of the
        # queue.  The decision whether to accept or not depends
        # on the current queue length and follows the Random
        # Early Discard algorithm.  When we accept it, we also
        # register a function to be called when the stream is
        # closed so that we can update the queue.  And we
        # immediately send a response.
        # When it's not the first time we see a stream, we just
        # take note that we owe it a response.  But we won't
        # respond until its queue position changes.
        #
        elif request.uri.startswith('/negotiate/'):
            if not stream in self.known:
                position = len(self.queue)
                min_thresh = CONFIG['negotiate.min_thresh']
                max_thresh = CONFIG['negotiate.max_thresh']
                if random.random() < float(position - min_thresh) / (
                                       max_thresh - min_thresh):
                    stream.close()
                    return
                self.queue.append(stream)
                self.known.add(stream)
                stream.atclose(self._update_queue)
                self._do_negotiate((stream, request, position))
            else:
                stream.opaque = request

        # For robustness
        else:
            raise RuntimeError('Unexpected URI')

    def _do_negotiate(self, baton):
        ''' Respond to a /negotiate request '''
        stream, request, position = baton

        module = request.uri.replace('/negotiate/', '')
        module = self.modules[module]
        request_body = json.load(request.body)

        parallelism = CONFIG['negotiate.parallelism']
        unchoked = int(position < parallelism)
        response_body = {
                         'queue_pos': position,
                         'real_address': stream.peername[0],
                         'unchoked': unchoked,
                        }
        if unchoked:
            extra = module.unchoke(stream, request_body)
            if not 'authorization' in extra:
                raise RuntimeError('Negotiate API violation')
            extra.update(response_body)
            response_body = extra
        else:
            response_body['authorization'] = ''

        response = Message()
        response.compose(code='200', reason='Ok',
                         body=json.dumps(response_body),
                         keepalive=True,
                         mimetype='application/json')
        stream.send_response(request, response)

    #
    # In theory this function should walk the queue and remove the
    # lost stream.  But, actually, it seems better/faster to create
    # and fill a new queue.
    # In the new queue we will add streams before @lost_stream and
    # streams after @lost_stream that (i) have no pending comet
    # request or (ii) have a pending comet request and successfully
    # manage to send it.
    # Note: in case of error sending the pending comet request,
    # unregister atclose hook to prevent recursion.
    # TODO Libero Camillo suggests to use an ordered dictionary to
    # implement the queue.  I like the idea and I will look into
    # that after the pending Neubot release.
    #
    def _update_queue(self, lost_stream, ignored):
        ''' Invoked when a connection is lost '''
        queue, found = collections.deque(), False
        position = 0
        for stream in self.queue:
            if not found:
                if lost_stream != stream:
                    position += 1
                    queue.append(stream)
                else:
                    found = True
                    self.known.remove(stream)
            elif not stream.opaque:
                position += 1
                queue.append(stream)
            else:
                request, stream.opaque = stream.opaque, None
                try:
                    self._do_negotiate((stream, request, position))
                    position += 1
                    queue.append(stream)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    logging.error('Exception', exc_info=1)
                    stream.unregister_atclose(self._update_queue)
                    self.known.remove(stream)
                    stream.close()
        self.queue = queue

# No poller, so it cannot be used directly
NEGOTIATE_SERVER = NegotiateServer(None)
