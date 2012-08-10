#!/usr/bin/env python

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
import sys
import unittest

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.http.message import Message
from neubot.negotiate.server import NEGOTIATE_SERVER
from neubot.negotiate.server import NegotiateServerModule
from neubot.negotiate.server import NegotiateServer

from neubot.compat import json

class MinimalHttpStream:
    ''' Minimal HTTP stream '''

    def __init__(self):
        ''' Initialize minimal HTTP stream '''
        self.response = None
        self.opaque = None
        self.peername = ('abc', 0)

    def send_response(self, request, response):
        ''' Pretend to send the response but actually just keep
            around a copy of it for later analysys '''
        self.response = response

    def close(self):
        ''' Pretend to close the stream '''

    def atclose(self, func):
        ''' Pretend to register atclose hook '''

    def unregister_atclose(self, func):
        ''' Pretend to unregister atclosed hook '''

class GotRequestHeaders(unittest.TestCase):

    ''' Verifies the behavior of got_request_headers() method
        of NEGOTIATE_SERVER '''

    def test_chunked(self):
        ''' Make sure we don't accept chunked requests '''
        message = Message()
        message['Transfer-Encoding'] = 'chunked'
        self.assertFalse(NEGOTIATE_SERVER.got_request_headers(None, message))

    def test_huge(self):
        ''' Make sure we don't accept big requests '''
        message = Message()
        message['Content-Length'] = str(1048576 + 1)
        self.assertFalse(NEGOTIATE_SERVER.got_request_headers(None, message))

    def test_negative(self):
        ''' Make sure we don't accept negative lengths '''
        message = Message()
        message['Content-Length'] = str(-1)
        self.assertRaises(
                          ValueError,
                          NEGOTIATE_SERVER.got_request_headers,
                          None, message
                         )

    def test_no_content_length(self):
        ''' Make sure we raise if there is no content-length '''
        self.assertRaises(
                          ValueError,
                          NEGOTIATE_SERVER.got_request_headers,
                          None, Message()
                         )

class ProcessRequest(unittest.TestCase):

    ''' Verifies the behavior of process_request() method
        of NEGOTIATE_SERVER '''

    def test_collect_no_module(self):
        ''' Verify that collect bails out when the module is unknown '''
        self.assertRaises(
                          KeyError,
                          NEGOTIATE_SERVER.process_request,
                          None, Message(uri='/collect/abc')
                         )

    def test_collect_no_json(self):
        ''' Verify that collect bails out when the body is not a JSON '''
        server = NegotiateServer(None)
        server.register_module('abc', None)
        self.assertRaises(
                          ValueError,
                          server.process_request,
                          None,
                          Message(uri='/collect/abc')
                         )


    def test_collect_successful(self):
        ''' Make sure the response is OK when collect succeeds '''

        server = NegotiateServer(None)
        server.register_module('abc', NegotiateServerModule())

        stream = MinimalHttpStream()
        request = Message(uri='/collect/abc')
        request.body = StringIO.StringIO('{}')

        server.process_request(stream, request)
        response = stream.response

        self.assertEqual(response.code, '200')
        self.assertEqual(response.reason, 'Ok')
        self.assertEqual(response.body, '{}')
        self.assertEqual(response['connection'], 'close')
        self.assertEqual(response['content-type'], 'application/json')

    def test_negotiate_delayed(self):
        ''' When a stream is already in queue the response is delayed '''

        server = NegotiateServer(None)
        stream = MinimalHttpStream()
        server.queue.append(stream)
        server.known.add(stream)

        request = Message(uri='/negotiate/')
        server.process_request(stream, request)

        self.assertEqual(stream.opaque, request)

    def test_negotiate_red(self):
        ''' Verify that random early discard works as expected '''

        server = NegotiateServer(None)
        server.register_module('abc', NegotiateServerModule())

        red_accepted, red_rejected, red_discarded = 0, 0, 0
        while True:

            # Create request and stream
            request = Message(uri='/negotiate/abc')
            request.body = StringIO.StringIO('{}')
            stream = MinimalHttpStream()

            # Should ALWAYS accept
            if len(server.queue) < CONFIG['negotiate.min_thresh']:
                server.process_request(stream, request)
                self.assertEquals(server.queue[-1], stream)

            # MAY accept or reject
            elif len(server.queue) < CONFIG['negotiate.max_thresh']:
                server.process_request(stream, request)
                if server.queue[-1] == stream:
                    red_accepted += 1
                else:
                    red_rejected += 1

            # MUST reject
            else:
                server.process_request(stream, request)
                self.assertNotEqual(server.queue[-1], stream)
                red_discarded += 1
                if red_discarded == 64:
                    break

        self.assertTrue(red_accepted > 0 and red_rejected > 0 and
                        red_discarded == 64)

    def test_negotiate_no_module(self):
        ''' Verify that negotiate bails out when the module is unknown '''
        self.assertRaises(
                          KeyError,
                          NEGOTIATE_SERVER.process_request,
                          MinimalHttpStream(),
                          Message(uri='/negotiate/abc')
                         )

    def test_negotiate_no_json(self):
        ''' Verify that negotiate bails out when the body is not a JSON '''
        server = NegotiateServer(None)
        server.register_module('abc', None)
        self.assertRaises(
                          ValueError,
                          server.process_request,
                          MinimalHttpStream(),
                          Message(uri='/negotiate/abc')
                         )


    def test_negotiate_successful(self):
        ''' Make sure the response is OK when negotiate succeeds '''

        server = NegotiateServer(None)
        server.register_module('abc', NegotiateServerModule())

        # Want to check authorized and nonauthorized streams
        for position in range(CONFIG['negotiate.parallelism'] + 3):

            stream = MinimalHttpStream()
            request = Message(uri='/negotiate/abc')
            request.body = StringIO.StringIO('{}')

            server.process_request(stream, request)
            response = stream.response

            self.assertEqual(response.code, '200')
            self.assertEqual(response.reason, 'Ok')
            self.assertNotEqual(response['connection'], 'close')
            self.assertEqual(response['content-type'], 'application/json')

            # Note: authorization is empty when you're choked
            body = json.loads(response.body)
            if position < CONFIG['negotiate.parallelism']:
                self.assertEqual(body, {
                                        u'unchoked': 1,
                                        u'queue_pos': position,
                                        u'real_address': u'abc',
                                        u'authorization': unicode(hash(stream))
                                       })
            else:
                self.assertEqual(body, {
                                        u'unchoked': 0,
                                        u'queue_pos': position,
                                        u'real_address': u'abc',
                                        u'authorization': u'',
                                       })

    def test_unexpected_uri(self):
        ''' Verify behavior when an unexpected URI is received '''
        self.assertRaises(
                          RuntimeError,
                          NEGOTIATE_SERVER.process_request,
                          None, Message(uri='/abc')
                         )

class NegotiateServerForUpdateQueue(NegotiateServer):

    ''' Negotiate server for UpdateQueue '''

    def __init__(self, poller):
        ''' Initialize negotiate server for UpdateQueue '''
        NegotiateServer.__init__(self, poller)
        self.negotiated = []

    def _do_negotiate(self, baton):
        ''' Pretend to respond to a /negotiate request '''
        if hasattr(baton[0], 'generate_error'):
            raise RuntimeError()
        else:
            self.negotiated.append(baton)

class UpdateQueue(unittest.TestCase):

    ''' Verifies the behavior of _update_queue() method
        of NEGOTIATE_SERVER '''

    def test_stream_before(self):
        ''' Verify what happens to a stream before the lost one '''

        server = NegotiateServerForUpdateQueue(None)
        for position in range(5):
            stream = MinimalHttpStream()
            server.queue.append(stream)
            server.known.add(stream)
            server.queue[-1].opaque = position

        server._update_queue(server.queue[-1], None)

        self.assertEqual(len(server.queue), 4)
        for position, stream in enumerate(server.queue):
            self.assertEqual(stream.opaque, position)
            self.assertTrue(stream in server.known)

    def test_stream_lost(self):
        ''' Verify what happens to the lost stream '''

        server = NegotiateServerForUpdateQueue(None)
        for _ in range(5):
            stream = MinimalHttpStream()
            server.queue.append(stream)
            server.known.add(stream)

        lost_stream = server.queue[3]
        server._update_queue(lost_stream, None)

        self.assertTrue(lost_stream not in server.queue)
        self.assertTrue(lost_stream not in server.known)

    def test_stream_after__no_send(self):
        ''' Verify what happens to streams after that don't have to send '''

        server = NegotiateServerForUpdateQueue(None)
        for _ in range(5):
            stream = MinimalHttpStream()
            server.queue.append(stream)
            server.known.add(stream)

        lost_stream = server.queue[2]
        server._update_queue(lost_stream, None)

        self.assertEqual(server.negotiated, [])

    def test_stream_after__send(self):
        ''' Verify what happens to streams after that has to send '''

        server = NegotiateServerForUpdateQueue(None)
        for position in range(5):
            stream = MinimalHttpStream()
            server.queue.append(stream)
            server.known.add(stream)
            stream.opaque = position

        lost_stream = server.queue[2]
        server._update_queue(lost_stream, None)

        self.assertEqual(server.negotiated, [
                                             (server.queue[2], 3, 2),
                                             (server.queue[3], 4, 3),
                                            ])

    def test_stream_after__error(self):
        ''' Verify what happens when a stream after raises an error '''

        server = NegotiateServerForUpdateQueue(None)
        for position in range(5):
            stream = MinimalHttpStream()
            server.queue.append(stream)
            server.known.add(stream)
            stream.opaque = position

        lost_stream = server.queue[2]
        server.queue[3].generate_error = True
        server._update_queue(lost_stream, None)

        self.assertEqual(server.negotiated, [
                                             (server.queue[2], 4, 2),
                                            ])

if __name__ == "__main__":
    unittest.main()
