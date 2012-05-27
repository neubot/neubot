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

from neubot.config import CONFIG
from neubot.net import stream

#
# Provide the bare minimum needed to look
# like a socket.  Raise on close(), send()
# and recv(): so we see when a function
# is invoked when we don't expect it.
# NOTE some tests use this class and others
# do not; and I believe the latter are
# easier to understand, so I should refactor
# the ones using this class.
#
class FakeSocket(object):

    def fileno(self):
        return -1
    def getsockname(self):
        return ('127.0.0.1', 8080)
    def getpeername(self):
        return ('127.0.0.1', 8080)

    def close(self):
        raise RuntimeError
    def send(self, octets):
        raise RuntimeError
    def recv(self, count):
        raise RuntimeError

#
# Set-up a stream and raise nearly for every-
# thing, so we seen when something unexpected is
# invoked.
# NOTE some tests use this class and others
# do not; and I believe the latter are
# easier to understand, so I should refactor
# the ones using this class.
#
class TestStream_Base(unittest.TestCase):
    def setUp(self):
        self.stream = stream.Stream(self)
        self.stream.attach(self, FakeSocket(), CONFIG)

    def connection_lost(self, stream):
        raise RuntimeError

    def close(self, stream):
        raise RuntimeError
    def set_readable(self, stream):
        raise RuntimeError
    def set_writable(self, stream):
        raise RuntimeError
    def unset_readable(self, stream):
        raise RuntimeError
    def unset_writable(self, stream):
        raise RuntimeError

#
#   ____  _
#  / ___|| |  ___   ___   ___
# | |    | | / _ \ / __| / _ \
# | |___ | || (_) |\__ \|  __/
#  \____||_| \___/ |___/ \___|
#
# Test the behavior of methods in the close path, that is
# when there is an exception or an explicit close.
#

#
# Our business in this section is close(), then
# re-arrange things so that close-related functions
# don't raise.
#
class TestStreamClose_Base(TestStream_Base):
    def close(self, stream):
        stream.handle_close()
    def connection_lost(self, stream):
        pass
    def setUp(self):
        TestStream_Base.setUp(self)
        self.stream.sock.soclose = lambda: None

#
# Make sure that close() moves us to close_complete
# when we're not sending.  While there, make sure it will
# invoke parent's connection_lost() method.
#
class TestStreamClose_Simple(TestStreamClose_Base):
    def runTest(self):
        self.assertFalse(self.stream.send_pending)
        self.lost = False
        self.stream.close()
        self.assertTrue(self.stream.close_complete)
        self.assertTrue(self.lost)

    def connection_lost(self, stream):
        self.lost = True

#
# Make sure that multiple handle_close() or close() after
# we have close()ed have no effect.
#
class TestStreamClose_Multiple(TestStreamClose_Base):
    def runTest(self):
        self.count = 0
        self.stream.close()
        self.stream.handle_close()
        self.stream.close()

    def connection_lost(self, stream):
        self.assertEqual(self.count, 0)
        self.count += 1

#
# Make sure our close function is robust with respect to
# one or both of send_pending and send_complete being True.
#
class TestStreamClose_NoEffect(TestStreamClose_Base):
    def runTest(self):
        for send_pending, close_complete in [(0,1), (1,0), (1,1)]:
            self.stream.send_pending = send_pending
            self.stream.close_complete = close_complete
            self.stream.close()

    def connection_lost(self, stream):
        raise RuntimeError

#
# Make sure that close() moves us to close_pending
# and not close_complete when we're already sending and
# the user invokes it.
#
class TestStreamClose_SendPending(TestStreamClose_Base):
    def runTest(self):
        self.stream.send_pending = True
        self.stream.close()
        self.assertFalse(self.stream.close_complete)
        self.assertTrue(self.stream.close_pending)

    def connection_lost(self, stream):
        raise RuntimeError

#
# Make sure that an error moves us into the close_complete
# state, expecially when we're not sending.
#
class TestStreamError_Simple(TestStreamClose_Base):
    def runTest(self):
        self.assertFalse(self.stream.send_pending)
        self.lost = False
        self.stream.handle_close()
        self.assertTrue(self.stream.close_complete)
        self.assertTrue(self.lost)

    def connection_lost(self, stream):
        self.lost = True

#
# Make sure that an error moves us into the close_complete
# state, even if we're sending.
#
class TestStreamError_SendPending(TestStreamClose_Base):
    def runTest(self):
        self.lost = False
        self.stream.send_pending = True
        self.stream.handle_close()
        self.assertTrue(self.stream.close_complete)
        self.assertTrue(self.lost)

    def connection_lost(self, stream):
        self.lost = True

#
# Make sure that multiple handle_close() or close() after
# we have handle_close() have no effect.
#
class TestStreamError_Multiple(TestStreamClose_Base):
    def runTest(self):
        self.count = 0
        self.stream.handle_close()
        self.stream.close()
        self.stream.handle_close()

    def connection_lost(self, stream):
        self.assertEqual(self.count, 0)
        self.count += 1

#
#  ____                     _
# |  _ \   ___   ___   ___ (_)__   __  ___
# | |_) | / _ \ / __| / _ \| |\ \ / / / _ \
# |  _ < |  __/| (__ |  __/| | \ V / |  __/
# |_| \_\ \___| \___| \___||_|  \_/   \___|
#
# Checks for the receive path, that includes the code
# you invoke when you want to receive and the code that
# is invoked when the underlying connection is ready.
#

#
# The first barrier is that we don't become readable if
# at least one of three conditions is met.
# If we're wrong the code will try to invoke None.set_readable
# which will raise an exception.
#
class TestStreamStartRecv_Barrier1(unittest.TestCase):
    def runTest(self):
        """Make sure start_recv honours pending and complete flags"""
        s = stream.Stream(None)
        for a,b,c in [(0,0,1),(0,1,0),(0,1,1),(1,0,0),(1,0,1),(1,1,0),(1,1,1)]:
            s.close_complete = a
            s.close_pending = b
            s.recv_pending = c
            s.start_recv()

#
# The second barrier is that we don't become readable
# if recv is "blocked" i.e. an SSL send operation is
# pending and preventing recv to run.
# If we're wrong the code will try to invoke None.set_readable
# which will raise an exception.
#
class TestStreamStartRecv_Barrier2(unittest.TestCase):
    def runTest(self):
        """Make sure start_recv() honours recv_blocked"""
        s = stream.Stream(None)
        s.recv_blocked = True
        s.start_recv()
        self.assertTrue(s.recv_pending)

#
# Make sure that readable() is _not_ invoked immediately
# just aftert start_recv().  It used to be in the past but
# now it's not the case anymore.
# If we're wrong self.sock.sorecv() is invoked and this
# will raise because self.sock = None.
#
class TestStreamStartRecv_WeNoInvokeReadableImmediately(unittest.TestCase):
    def runTest(self):
        """Make sure start_recv does not invoked readable directly"""
        s = stream.Stream(self)
        self.isreadable = False
        s.start_recv()
        self.assertTrue(self.isreadable)

    def set_readable(self, stream):
        self.isreadable = True

#
# Make sure that, when ssl needs kickoff, sorecv() is
# actually invoked, so we can start the SSL negotiation
# and there is no starvation.
#
class TestStreamStartRecv_SSLKickOff(unittest.TestCase):
    def runTest(self):
        """Make sure we kick off SSL on the server side"""
        s = stream.Stream(self)
        s.recv_ssl_needs_kickoff = True
        s.sock = self
        self.isreadable = False
        self.has_read = False
        s.start_recv()
        self.assertTrue(self.isreadable)
        self.assertTrue(self.has_read)

    def set_readable(self, stream):
        self.isreadable = True

    def sorecv(self, n):
        self.has_read = True
        return stream.WANT_READ, ""

class TestStreamReadable_RecvBlocked_RecvPending(TestStream_Base):
    def runTest(self):
        self.count = 0
        self.stream.sock.sorecv = lambda k: (45,"")     #XXX
        self.stream.handle_write = lambda: None
        self.stream.recv_blocked = True
        self.stream.recv_pending = True
        self.stream.handle_read()
        self.assertEqual(self.count, 1)

    def set_writable(self, stream):
        self.count += 1

class TestStreamReadable_RecvBlocked_NoRecvPending(TestStream_Base):
    def runTest(self):
        self.count = 0
        self.stream.sock.sorecv = lambda k: (45,"")     #XXX
        self.stream.handle_write = lambda: None
        self.stream.recv_blocked = True
        self.stream.handle_read()
        self.assertEqual(self.count, 2)

    def set_writable(self, stream):
        self.count += 1

    def unset_readable(self, stream):
        self.count += 1

class TestStreamReadable_SuccessBytes(TestStream_Base):
    def runTest(self):
        self.count = 0
        self.stream.sock.sorecv = lambda k: (stream.SUCCESS, "abc")
        self.stream.handle_write = lambda: 1/0
        self.stream.recv_complete = self.recv_complete
        self.stream.handle_read()
        self.assertEqual(self.count, 2)
        self.assertFalse(self.stream.recv_pending)

    def unset_readable(self, stream):
        self.count += 1

    def recv_complete(self, octets):
        self.assertEqual(octets, "abc")
        self.count += 1

class TestStreamReadable_WantRead(TestStream_Base):
    def runTest(self):
        self.stream.sock.sorecv = lambda k: (stream.WANT_READ, "")
        self.stream.handle_write = lambda: 1/0
        self.stream.handle_read()

class TestStreamReadable_WantWrite(TestStream_Base):
    def runTest(self):
        self.stream.sock.sorecv = lambda k: (stream.WANT_WRITE, "")
        self.stream.handle_write = lambda: 1/0
        self.stream.handle_read()

    def unset_readable(self, stream):
        pass

    def set_writable(self, stream):
        pass

class TestStreamReadable_EOF(TestStream_Base):
    def runTest(self):
        self.stream.sock.sorecv = lambda k: (stream.SUCCESS, "")
        self.stream.handle_write = lambda: 1/0
        self.stream.handle_read()
        self.assertTrue(self.stream.eof)

    def close(self, stream):
        pass

class TestStreamReadable_Error(TestStream_Base):
    def runTest(self):
        self.stream.sock.sorecv = lambda k: (stream.ERROR, RuntimeError())
        self.stream.handle_write = lambda: 1/0
        self.assertRaises(RuntimeError, self.stream.handle_read)

class TestStreamReadable_UnknownStatus(TestStream_Base):
    def runTest(self):
        self.stream.sock.sorecv = lambda k: (58, "")
        self.stream.handle_write = lambda: 1/0
        self.assertRaises(RuntimeError, self.stream.handle_read)

#
#  ____                    _
# / ___|   ___  _ __    __| |
# \___ \  / _ \| '_ \  / _` |
#  ___) ||  __/| | | || (_| |
# |____/  \___||_| |_| \__,_|
#
# Here is the code to make sure that the send-path remains
# consistent while we proceed in time.
#

#
# Make sure that at the beginning the send queue is empty
# and that it continues to look like that when we push
# empty data to it.
#
class TestStreamSend_ReadSendQueue_Empty(unittest.TestCase):
    def runTest(self):
        """Make sure send queue starts empty and remains empty if we push ''"""
        s = stream.Stream(None)
        self.assertEqual(s.read_send_queue(), "")
        s.start_send("")
        self.assertEqual(s.read_send_queue(), "")
        s.start_send(StringIO.StringIO(""))
        self.assertEqual(s.read_send_queue(), "")

#
# Push data into the send_queue and the pull it out and
# make sure that we ge the same result.
# Note that we push strings, StringIOs and empty strings.
# The latter to be sure they not create issues, i.e.
# they're not taken as a signal that we're done when we
# are not.
#
class TestStreamSend_ReandSendQueue_NotEmpty(unittest.TestCase):
    def runTest(self):
        """Gain confidence that the send queue is not buggy"""
        s = stream.Stream(self)

        # Generate messages
        messages = []
        for _ in range(4096):
            ln = random.randrange(0, 4096)
            patt = random.randrange(32, 127)
            sio = random.random() < 0.5
            strstr = chr(patt) * ln
            if sio:
                messages.append(StringIO.StringIO(strstr))
            else:
                messages.append(strstr)
        # Empty messages might cause issues
        for _ in range(4096):
            messages.append("")
        random.shuffle(messages)

        # This is what we expect
        expected = []
        for m in messages:
            if isinstance(m, basestring):
                expected.append(m)
            else:
                expected.append(m.read())
                m.seek(0)                       #XXX

        # Fill
        for m in messages:
            s.start_send(m)

        # Read send queue
        output = [s.send_octets]                #XXX
        while True:
            buf = s.read_send_queue()
            if not buf:
                break
            output.append(buf)

        # Make sure it matches
        self.assertEqual("".join(expected), "".join(output))

    # Invoked by
    def set_writable(self, stream):
        pass

if __name__ == "__main__":
    unittest.main()
