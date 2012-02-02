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
import struct
import sys
import unittest

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.bittorrent import stream

#
#   ____                     _       _
#  / ___|  ___   _ __   ___ (_) ___ | |_   ___  _ __    ___  _   _
# | |     / _ \ | '_ \ / __|| |/ __|| __| / _ \| '_ \  / __|| | | |
# | |___ | (_) || | | |\__ \| |\__ \| |_ |  __/| | | || (__ | |_| |
#  \____| \___/ |_| |_||___/|_||___/ \__| \___||_| |_| \___| \__, |
#                                                            |___/
#
# This section includes some consistency checks.
#

#
# Make sure that each message has a value that
# corresponds to chr() of the index of such message
# into the vector of messages.
#
class TestMessageTypes(unittest.TestCase):
    def runTest(self):
        """Make sure that message types are consistent"""
        for idx, value in enumerate(stream.MESSAGES):
            self.assertEqual(chr(idx), value)
        self.assertEqual(stream.MESSAGESET,
          set(stream.MESSAGES))

#
# Make sure that we have an invalid-length rule for
# each message and viceversa.
#
class TestMessageLengths(unittest.TestCase):
    def runTest(self):
        """Make sure that invalid-lenght rules are consistent"""
        self.assertTrue(stream.MESSAGESET ==
          set(stream.INVALID_LENGTH.keys()))

#
#  ____                                           _      _
# |  _ \   ___   __ _  ___  ___   ___  _ __ ___  | |__  | |  ___  _ __
# | |_) | / _ \ / _` |/ __|/ __| / _ \| '_ ` _ \ | '_ \ | | / _ \| '__|
# |  _ < |  __/| (_| |\__ \\__ \|  __/| | | | | || |_) || ||  __/| |
# |_| \_\ \___| \__,_||___/|___/ \___||_| |_| |_||_.__/ |_| \___||_|
#
# This section contains code that stimulates the incoming messages
# reassembler.
#

#
# This class prepares a set of variable-length messages, including
# also some keepalives and arranges things so that it's possible to
# collect what the reassembler have read.
# It's up to subclasses to decide how to feed the reassembler, and
# for sure it's relevant to use different techniques.
# This class also provides subclasses functionalities to compare
# input stimuli with what the reassembler has read.
#
class TestReassembler_Base(unittest.TestCase):

    def setUp(self):
        self.stream = stream.StreamBitTorrent(self)
        self.saved_messages = []
        self.messages = []
        self.partial_message = []

        # Re-route send/recv calls
        self.stream._got_message = self.got_message
        self.stream.start_send = self.start_send

        for _ in range(4096):
            m = random.randrange(0, 4096) * "A"
            self.stream._send_message(m)
        # Keepalives might appear here and there
        for _ in range(512):
            self.stream._send_message("")
        random.shuffle(self.messages)

        # XXX The handshake makes things much more complex
        self.stream.left = 0

        # We want to test diversion of big messages too
        self.stream.smallmessage = 2048
        self.stream._got_message_start = self.got_message_start
        self.stream._got_message_part = self.got_message_part
        self.stream._got_message_end = self.got_message_end

    # XXX Trust the code that prepares messages
    def start_send(self, s):
        self.messages.append(s)

    # For big messages
    def got_message_start(self, m):
        if self.partial_message:
            raise RuntimeError("big messages error")
        self.partial_message.append(m)                  # should be string
    def got_message_part(self, m):
        self.partial_message.append(str(m))             # should be buffer
    def got_message_end(self):
        if not self.partial_message:
            raise RuntimeError("big messages error")
        self.saved_messages.append("".join(self.partial_message))
        del self.partial_message[:]

    # Ordinary messages
    def got_message(self, message):
        self.saved_messages.append(message)

    def set_readable(self, stream):
        pass

    def check_results(self):

        # Zap length, KEEPALIVEs
        v = []
        for m in self.messages:
            m = m[4:]
            if not m:
                continue
            v.append(m)
        self.messages = v

        # Check equality, final state was reached, etc.
        self.assertEqual(self.messages, self.saved_messages)
        self.assertEqual(self.stream.left, 0)

# Receive each message independently on the others
class TestReassembler_Independent(TestReassembler_Base):
    def runTest(self):
        """Gain confidence that the reader works with separate messages"""
        for m in self.messages:
            self.stream.recv_complete(m)
        self.check_results()

# Receive all the messages in a single buffer
class TestReassembler_Buffer(TestReassembler_Base):
    def runTest(self):
        """Gain confidence that the reader works with a single buffer"""
        self.stream.recv_complete("".join(self.messages))
        self.check_results()

# Receive the messages byte after byte
class TestReassembler_SingleChar(TestReassembler_Base):
    def runTest(self):
        """Gain confidence that the reader works with small reads"""
        amt = 17                                        #XXX trade-off
        m = "".join(self.messages)
        while m:
            self.stream.recv_complete(m[:amt])
            m = buffer(m, amt)
        self.check_results()

#
#  ____
# |  _ \   __ _  _ __  ___   ___  _ __
# | |_) | / _` || '__|/ __| / _ \| '__|
# |  __/ | (_| || |   \__ \|  __/| |
# |_|     \__,_||_|   |___/ \___||_|
#
# This section contains tests for the code that parses and
# dispatches incoming messages.
#

#
# Make sure that we behave properly when we receive
# a new incoming handshake.
#
class GotMessageHandshake(unittest.TestCase):
    def runTest(self):
        """Make sure we behave properly upon receiving an handshake"""

        # Test check on length
        for l in set(range(128)) - set([68]):
            s = stream.StreamBitTorrent(None)
            self.assertRaises(RuntimeError, s._got_message, "A" * l)

        # Check protocol name length
        for l in set(range(256)) - set([19]):
            s = stream.StreamBitTorrent(None)
            m = [chr(l), "A" * 67]
            self.assertRaises(RuntimeError, s._got_message, "".join(m))

        # Check protocol name (XXX stupid check)
        for pn in ["BitTorrent protocoX", "XitTorrent protocol"]:
            s = stream.StreamBitTorrent(None)
            m = [chr(19), pn, "A" * 48]
            self.assertRaises(RuntimeError, s._got_message, "".join(m))

        # Is connection_ready invoked?
        self.invoked_connection_ready = False
        s = stream.StreamBitTorrent(None)
        s.parent = self
        #
        # XXX With this infohash and my_id we play the role of
        # the connector: the listener instead would send an hand-
        # shake upon receiving an hanshake and the test would
        # fail because here poller is None (see above).
        #
        self.infohash = chr(0) * 20
        self.my_id = chr(0) * 20
        m = [chr(19), "BitTorrent protocol", chr(0) * 48]
        s._got_message("".join(m))
        self.assertEqual(self.invoked_connection_ready, True)

    def connection_ready(self, s):
        self.invoked_connection_ready = True

#
# Make sure that invalid message codes cannot sneak in, that
# we reject messages with invalid length, and that there is an
# error if we receive the bitfield after we've got something.
#
class TestOtherMessagesProcessing(unittest.TestCase):
    def runTest(self):
        """Make sure we correctly process BT messages"""
        self.numpieces = 1024
        s = stream.StreamBitTorrent(None)
        s.parent = self

        # I.e. we've already done the handshake
        s.complete = True

        # Catch invalid types
        for t in range(len(stream.MESSAGES), 256):
            self.assertRaises(RuntimeError, s._got_message, chr(t))

        # Length must be 1
        for t in [stream.CHOKE, stream.UNCHOKE, stream.INTERESTED,
                  stream.NOT_INTERESTED]:
            for ln in range(1, 128):
                m = "".join([t, "A" * ln])
                self.assertRaises(RuntimeError, s._got_message, m)

        # Length must be 5
        for ln in set(range(128)) - set([5]):
            m = "".join([stream.HAVE, "0" * ln])
            self.assertRaises(RuntimeError, s._got_message, m)
        for idx in range(self.numpieces * 2):
            m = "".join([stream.HAVE, struct.pack("!I", idx)])
            if idx < self.numpieces:
                s._got_message(m)
            else:
                self.assertRaises(RuntimeError, s._got_message, m)

        # Length must be > 1
        s.got_anything = False
        for ln in range(256):
            s.got_anything = False
            m = "".join([stream.BITFIELD, "A" * ln])
            if ln == 0:
                self.assertRaises(RuntimeError, s._got_message, m)
            else:
                s._got_message(m)
        # Should fail because we've got something
        self.assertRaises(RuntimeError, s._got_message, m)

        # Length must be 13
        for t in [stream.REQUEST, stream.CANCEL]:
            for ln in set(range(128)) - set([13]):
                m = "".join([t, "0" * ln])
                self.assertRaises(RuntimeError, s._got_message, m)
            for idx in range(self.numpieces * 2):
                m = "".join([t, struct.pack("!III", idx, 0, 0)])
                if idx < self.numpieces:
                    s._got_message(m)
                else:
                    self.assertRaises(RuntimeError, s._got_message, m)

        # Length must be > 9
        for ln in range(10):
            m = "".join([stream.PIECE, "0" * ln])
            self.assertRaises(RuntimeError, s._got_message, m)
        for idx in range(self.numpieces * 2):
            m = "".join([stream.PIECE, struct.pack("!II", idx, 0), "A" * 3])
            if idx < self.numpieces:
                s._got_message(m)
            else:
                self.assertRaises(RuntimeError, s._got_message, m)

    # Peer iface
    def got_choke(self, s):
        pass
    def got_unchoke(self, s):
        pass
    def got_interested(self, s):
        pass
    def got_not_interested(self, s):
        pass
    def got_have(self, i):
        pass
    def got_bitfield(self, b):
        pass
    def got_request(self, s, i, a, b):
        pass
#   def got_cancel(self, s, i, a, b):  # not yet
#       pass
    def got_piece(self, s, i, a, b):
        pass

if __name__ == "__main__":
    unittest.main()
