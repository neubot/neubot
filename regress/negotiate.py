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
import random
import sys
import unittest

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.http.message import Message
from neubot.net.stream import Stream

from neubot.compat import json
from neubot.negotiate import _Negotiator
from neubot.negotiate import _SERVER
from neubot.negotiate import _ServerNegotiate
from neubot.negotiate import NEGOTIATOR
from neubot.negotiate import NegotiatorModule
from neubot.negotiate import NegotiatorEOF
from neubot.negotiate import sha1stream

from neubot import utils

#
#  _   _ _____ _____ ____    _
# | | | |_   _|_   _|  _ \  | |    __ _ _   _  ___ _ __
# | |_| | | |   | | | |_) | | |   / _` | | | |/ _ \ '__|
# |  _  | | |   | | |  __/  | |__| (_| | |_| |  __/ |
# |_| |_| |_|   |_| |_|     |_____\__,_|\__, |\___|_|
#                                       |___/
#
# Unit tests for the HTTP layer of negotiation.
#

class HTTP_GotRequestHeaders(unittest.TestCase):

    def test_chunked(self):
        """Make sure we don't accept chunked requests"""
        message = Message()
        message["Transfer-Encoding"] = "chunked"
        self.assertFalse(_SERVER.got_request_headers(None, message))

    def test_huge(self):
        """Make sure we don't accept huge requests"""
        message = Message()
        message["Content-Length"] = str(1048576 +1)
        self.assertFalse(_SERVER.got_request_headers(None, message))

    def test_negative(self):
        """Make sure we don't accept negative lengths"""
        message = Message()
        message["Content-Length"] = str(-1)
        self.assertRaises(ValueError, _SERVER.got_request_headers,
                                      None, message)

    def test_no_content_length(self):
        """Make sure we raise if there is no content-length"""
        message = Message()
        self.assertRaises(ValueError, _SERVER.got_request_headers,
                                      None, message)

class HTTP_GotRequest(unittest.TestCase):

    def test_404(self):
        """Verify behavior when the URI is unhandled"""

        message = Message(uri="/abc")

        server = _ServerNegotiate(None)
        server.send_response = lambda m: \
          self.assertEquals(m, {
                                "code": "404",
                                "keepalive": False,
                                "mimetype": "text/plain",
                                "reason": "Not Found",
                                "response_body": "Not Found",
                                "ident": sha1stream(None),
                                "request_body": {},
                                "request": message,
                                "parent": server,
                                "stream": None,
                               })

        server.process_request(None, message)

    def test_200_negotiate(self):
        """Verify behavior when the URI is /negotiate"""

        server = _ServerNegotiate(None)
        server.negotiator = _Negotiator()

        message = Message(uri="/negotiate/abc")

        server.negotiator.negotiate = lambda m: \
          self.assertEquals(m, {
                                "code": "200",
                                "keepalive": True,
                                "mimetype": "application/json",
                                "reason": "Ok",
                                "response_body": "",
                                "ident": sha1stream(None),
                                "request_body": {},
                                "request": message,
                                "parent": server,
                                "stream": None,
                                "module": "abc",
                               })

        #
        # Since send_response() should not be invoked, make
        # a wrong comparison so that we notice it if the func
        # is invoked unexpectedly.
        #
        server.send_response = lambda m: \
          self.assertEquals(m, {})

        server.process_request(None, message)

    def test_200_collect(self):
        """Verify behavior when the URI is /collect"""

        server = _ServerNegotiate(None)
        server.negotiator = _Negotiator()

        message = Message(uri="/collect/abc")

        func = lambda m: \
          self.assertEquals(m, {
                                "code": "200",
                                "keepalive": True,
                                "mimetype": "application/json",
                                "reason": "Ok",
                                "response_body": "",
                                "ident": sha1stream(None),
                                "request_body": {},
                                "request": message,
                                "parent": server,
                                "stream": None,
                                "module": "abc",
                               })

        #
        # In this case, differently from negotiate, both
        # functions are invoked so make sure they both receive
        # what we expect.
        #
        server.negotiator.collect = func
        server.send_response = func

        server.process_request(None, message)

    def test_body_invalid_mime(self):
        """Make sure we raise RuntimeError if the MIME type is wrong"""

        server = _ServerNegotiate(None)
        server.negotiator = _Negotiator()

        message = Message()
        message.compose(pathquery="/collect/abcdefg",
                        body=StringIO.StringIO("abc"))

        self.assertRaises(RuntimeError, server.process_request, None, message)

        message = Message()
        message.compose(pathquery="/collect/abcdefg",
                        body=StringIO.StringIO("abc"),
                        mimetype="text/plain")

        self.assertRaises(RuntimeError, server.process_request, None, message)

    def test_body_not_a_dictionary(self):
        """Make sure we raise ValueError if we cannot parse request body"""

        server = _ServerNegotiate(None)
        server.negotiator = _Negotiator()

        message = Message()
        message.compose(pathquery="/collect/abcdefg",
                        body=StringIO.StringIO("abc"),
                        mimetype="application/json")

        self.assertRaises(ValueError, server.process_request, None, message)

    def test_body_a_dictionary(self):
        """Make sure we correctly read incoming dictionaries"""

        server = _ServerNegotiate(None)
        server.negotiator = _Negotiator()

        d = {"abc": 12, "k": "s", "uuu": 1.74}

        server.send_response = lambda m: self.assertEquals(d,
          m["request_body"])

        message = Message()
        message.compose(pathquery="/collect/abcdefg",
                        body=StringIO.StringIO(json.dumps(d)),
                        mimetype="application/json")

        server.process_request(None, message)

    def test_body_empty(self):
        """Make sure we correctly read empty incoming bodies"""

        server = _ServerNegotiate(None)
        server.negotiator = _Negotiator()

        d = {}

        server.send_response = lambda m: self.assertEquals(d,
          m["request_body"])

        message = Message()
        message.compose(pathquery="/collect/abcdefg")

        server.process_request(None, message)

#
#  _   _                  _   _       _
# | \ | | ___  __ _  ___ | |_(_) __ _| |_ ___  _ __
# |  \| |/ _ \/ _` |/ _ \| __| |/ _` | __/ _ \| '__|
# | |\  |  __/ (_| | (_) | |_| | (_| | || (_) | |
# |_| \_|\___|\__, |\___/ \__|_|\__,_|\__\___/|_|
#             |___/
#
# Unit test for the common negotiator code.
#

class Negotiator_Register(unittest.TestCase):
    def runTest(self):
        """Check that register() works"""
        mod = object()
        negotiator = _Negotiator()
        negotiator.register("abc", mod)
        self.assertEquals(negotiator._mods["abc"], mod)

class Negotiator_NegotiatorRED(unittest.TestCase):

    def test_below_min(self):
        """Verify behavior when len(queue) < MIN"""
        n = _Negotiator()
        for _ in range(int(n._red)):
            n._queue.append(None)
            #
            # Reject if rnd() < threshold where threshold is
            # less than 0 when len(queue) < MIN.
            #
            reject = n._random_early_discard(rnd=lambda: 0)
            self.assertFalse(reject)

    def test_between_min_and_max(self):
        """Verify behavior when MIN < len(queue) < MAX"""
        v = [0, 0]

        n = _Negotiator()
        for idx in range(2 * int(n._red)):
            n._queue.append(None)
            if idx > n._red:
                reject = n._random_early_discard()
                v[reject] += 1

        self.assertTrue(v[0] > 0 and v[1] > 0)

    def test_above_max(self):
        """Verify behavior when len(queue) > MAX"""
        n = _Negotiator()
        for _ in range(2 * int(n._red)):
            n._queue.append(None)
        n._queue.append(None)
        #
        # Reject if rnd() < threshold where threshold is
        # more than 1 when len(queue) > MAX.
        #
        reject = n._random_early_discard(rnd=lambda: 1)
        self.assertTrue(reject)

class Negotiator_Negotiate(unittest.TestCase):

    def test_negotiate_except(self):
        """Verify negotiate raises KeyError if the module is unknown"""
        stream = Stream(None)
        stream.peername = ("abc", 3456)

        m = {
             "stream": stream,
             "ident": sha1stream(stream),
             "module": "abc",
            }

        negotiator = _Negotiator()
        self.assertRaises(KeyError, negotiator.negotiate, m)

    def test_negotiate_add(self):
        """Verify negotiate behavior when we add a new stream"""
        stream = Stream(None)
        stream.peername = ("abc", 3456)

        m = {
             "stream": stream,
             "ident": sha1stream(stream),
             "module": "abc",
            }

        negotiator = _Negotiator()
        negotiator._finalize_response = lambda m, ln: None
        negotiator._send_response = lambda m: None
        negotiator.register("abc", None)

        negotiator.negotiate(m)

        # Do we keep track of the new stream?
        self.assertTrue(stream in negotiator._queue)
        self.assertTrue(stream in negotiator._known)

        # Is the watchdog correctly initialized?
        self.assertTrue(negotiator._at_close in stream.atclosev)
        self.assertTrue(utils.ticks() - stream.created < 1)             #XXX

    def test_negotiate_delay(self):
        """Verify negotiate behavior when we delay response"""
        stream = Stream(None)
        stream.peername = ("abc", 3456)

        m = {
             "stream": stream,
             "ident": sha1stream(stream),
             "module": "abc",
            }

        negotiator = _Negotiator()
        negotiator._finalize_response = lambda m, ln: None
        negotiator._send_response = lambda m: None
        negotiator.register("abc", None)

        for _ in range(2):
            negotiator.negotiate(m)

        self.assertTrue(stream in negotiator._delay)

class Negotiator_Collect(unittest.TestCase):
    def test_key_error(self):
        """Verify collect() raises KeyError if the module name is unknown"""
        self.assertRaises(KeyError, NEGOTIATOR.collect, {"module": "abc"})

class Negotiator_AtClose(unittest.TestCase):

    def test_at_close(self):
        """Verify _at_close() works as expected"""
        negotiator = _Negotiator()
        negotiator._finalize_response = lambda m, ln: None
        negotiator._send_response = lambda m: None
        negotiator.register("abc", None)

        for _ in range(3):
            stream = Stream(self)
            stream.peername = ("abc", 3456)

            m = {
                 "stream": stream,
                 "ident": sha1stream(stream),
                 "module": "abc",
                }

            # To test the delay queue too
            for _ in range(2):
                negotiator.negotiate(m)

        negotiator._at_close(stream, None)
        self.assertTrue(stream not in negotiator._queue)
        self.assertTrue(stream not in negotiator._known)
        self.assertTrue(stream not in negotiator._delay)

        self.assertTrue(len(negotiator._delay) == 0)

class Negotiator_FinalizeResponse(unittest.TestCase):

    def test_unchoke(self):
        """Verify finalize_response() when unchoke"""

        dummy = [False]
        module = NegotiatorModule()
        module.unchoke = lambda m: dummy.pop()

        negotiator = _Negotiator()
        negotiator.register("abc", module)

        m = { "response_body": {}, "module": "abc" }
        negotiator._finalize_response(m, 0)

        self.assertEqual(json.loads(m["response_body"]),
               { u"unchoked": True, u"queue_pos": 0 })
        self.assertEqual(len(dummy), 0)

    def test_choke(self):
        """Verify finalize_response() when choke"""

        dummy = [False]
        module = NegotiatorModule()
        module.unchoke = lambda m: dummy.pop()

        negotiator = _Negotiator()
        negotiator.register("abc", module)

        m = { "response_body": {}, "module": "abc" }
        negotiator._finalize_response(m, 21)

        self.assertEqual(json.loads(m["response_body"]),
               { u"unchoked": False, u"queue_pos": 21 })
        self.assertEqual(len(dummy), 1)

#
#  ____  _                 _       _   _
# / ___|(_)_ __ ___  _   _| | __ _| |_(_) ___  _ __
# \___ \| | '_ ` _ \| | | | |/ _` | __| |/ _ \| '_ \
#  ___) | | | | | | | |_| | | (_| | |_| | (_) | | | |
# |____/|_|_| |_| |_|\__,_|_|\__,_|\__|_|\___/|_| |_|
#
# Simulate randomly and poorly the behavior of a number
# of connections to see what happens
#

# To attach attributes to an object
class Object(object):
    pass

# We need a fake poller for when we close the stream
class FakePoller(object):
    def close(self, stream):
        stream.handle_close()

# We need to emulate one or more negotiator modules
class FakeNegotiatorModule(NegotiatorModule):
    def __init__(self):
        self._allow = set()

    def unchoke(self, m):
        # Multiple negotiation are possible
        if m["stream"] not in self._allow:
            self._allow.add(m["stream"])
            m["stream"].atclose(self._atclose)

    def _atclose(self, stream, exception):
        self._allow.remove(stream)

    def collect(self, m):
        if m["stream"] not in self._allow:
            raise NegotiatorEOF()

class Simulation(unittest.TestCase):

    def runTest(self):
        """Simulate clients behavior to stress the Negotiator"""

        # Log file
        #fp = open("simulation.txt", "w")

        # Fake negotiator
        negotiator = _Negotiator()
        negotiator.register("A", FakeNegotiatorModule())
        negotiator.register("B", FakeNegotiatorModule())
        negotiator.register("C", FakeNegotiatorModule())

        # Simulated streams
        streams = []
        for _ in range(8192):
            stream = Stream(FakePoller())
            stream.parent = Object()
            stream.parent.connection_lost = lambda s: None
            stream.sock = Object()
            stream.sock.soclose = lambda: None
            stream.peername = str((str(hash(stream)), 7))
            stream.logname = str((str(hash(stream)), 7))
            streams.append(stream)

        # Track streams we have notified
        notified = set()
        self.send_response = lambda m: notified.add(m["stream"])

        # Track streams that have negotiated
        negotiated = set()

        while streams:
            #
            # Select stream
            #
            idx = random.randrange(len(streams))
            stream = streams[idx]

            #
            # Select event
            # 60% negotiate 20% collect 20% close
            #
            rnd = random.random()
            if rnd < 0.6:

                # Negotiate
                m = {
                     "stream": stream,
                     "ident": sha1stream(stream),
                     "module": chr(random.randrange(ord("A"), ord("A") +3)),
                     "parent": self,    #XXX
                    }

                notified.clear()

                # EOF if random early discard
                try:
                    negotiator.negotiate(m)
                except NegotiatorEOF:
                    #fp.write("%s random-early-discard\n" % sha1stream(stream))
                    streams.remove(stream)
                    stream.close()
                else:
                    self.assertTrue(stream in negotiator._queue)
                    self.assertTrue(stream in negotiator._known)

                    # Not notified?  So must be in the delayed queue
                    if stream not in notified:
                        #fp.write("%s negotiate-delay\n" % sha1stream(stream))
                        self.assertTrue(stream in negotiator._delay)
                    else:
                        #fp.write("%s negotiate-send\n" % sha1stream(stream))
                        pass

                    negotiated.add(stream)

            elif rnd < 0.8:

                # Collect
                m = {
                     "stream": stream,
                     "request_body": "{}",
                     "module": chr(random.randrange(ord("A"), ord("A") +3)),
                     "response_body": "",
                    }

                # EOF if not authorized
                try:
                    negotiator.collect(m)
                except NegotiatorEOF:
                    #fp.write("%s collect-no-auth\n" % sha1stream(stream))
                    streams.remove(stream)
                    stream.close()
                else:
                    #fp.write("%s collect-ok\n" % sha1stream(stream))
                    pass

            else:
                # XXX Don't waste streams w/o a good reason
                if stream not in negotiated:
                    continue

                #fp.write("%s close\n" % sha1stream(stream))
                streams.remove(stream)

                # Remember streams to be notified
                orig = set(negotiator._delay.keys())
                notified.clear()

                stream.close()

                # Make sure we removed stream
                self.assertTrue(stream not in negotiator._queue)
                self.assertTrue(stream not in negotiator._known)
                self.assertTrue(stream not in negotiator._delay)

                # Make sure we notified all
                self.assertEqual(notified, orig - set([stream]))

        # Make sure negotiator is empty
        self.assertEqual(len(negotiator._queue), 0)
        self.assertEqual(len(negotiator._known), 0)
        self.assertEqual(len(negotiator._delay), 0)

        # Make sure modules are empty
        self.assertEqual(len(negotiator._mods["A"]._allow), 0)
        self.assertEqual(len(negotiator._mods["B"]._allow), 0)
        self.assertEqual(len(negotiator._mods["C"]._allow), 0)

if __name__ == "__main__":
    unittest.main()
