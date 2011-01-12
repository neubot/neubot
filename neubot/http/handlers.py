# neubot/http/handlers.py

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
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

#
# Protocol handler
#

from StringIO import StringIO
from neubot.utils import file_length
from neubot.net.pollers import sched
from collections import deque
from neubot import log

class Receiver:
    def closing(self):
        pass

    def progress(self, data):
        pass

    def got_request_line(self, method, uri, protocol):
        pass

    def got_response_line(self, protocol, code, reason):
        pass

    def got_header(self, key, value):
        pass

    def end_of_headers(self):
        pass

    def got_piece(self, piece):
        pass

    def end_of_body(self):
        pass

# Possible states of the receiver
(IDLE, BOUNDED, UNBOUNDED, CHUNK, CHUNK_END, FIRSTLINE,
 HEADER, CHUNK_LENGTH, TRAILER, ERROR) = range(0,10)

# Accepted HTTP protocols
PROTOCOLS = ["HTTP/1.0", "HTTP/1.1"]

# Maximum allowed line length
MAXLINE = 1<<19

# flags
ISCLOSED = 1<<0

class Handler:

    #
    # We use a list for reading because we need to append and iterate
    # through the list, but we use a deque for writing because we need
    # to popleft().
    # In passiveclose() we schedule close() 30 seconds in the future
    # because we noticed problems using 1 second and we want to stay
    # on the safe side--BTW it's not clear to me why this happens and
    # I will spend some effort to learn the reason soon.
    #

    def __init__(self, stream, receiver):
        self.stream = stream
        self.stream.notify_closing = self._closing
        self.flags = 0
        self.task = None
        # sending
        self.sendqueue = deque()
        self.flush_success = None
        self.flush_progress = None
        self.flush_error = None
        # receiving
        self.incoming = []
        self.receiver = receiver
        self.left = 0
        self.state = FIRSTLINE

    def __del__(self):
        pass

    def passiveclose(self):
        if not (self.flags & ISCLOSED):
            self.task = sched(30, self.close)
            self.state = IDLE

    def close(self, check_eof=False):
        if not (self.flags & ISCLOSED):
            self.flags |= ISCLOSED
            if self.task:
                self.task.unsched()
                self.task = None
            if self.receiver:
                if check_eof and self.stream.eof and self.state == UNBOUNDED:
                    self.receiver.end_of_body()
                self.receiver.closing()
                self.receiver = None
            if self.flush_error:
                self.flush_error()
            self.flush_success = None
            self.flush_progress = None
            self.flush_error = None
            self.stream.close()
            self.stream.notify_closing = None
            self.stream = None

    def _closing(self):
        self.close(check_eof=True)

    #
    # bufferize/flush
    #

    def bufferize(self, x):
        if not (self.flags & ISCLOSED):
            self.sendqueue.append(x)

    def flush(self, flush_success, flush_progress=None, flush_error=None):
        if not (self.flags & ISCLOSED):
            self.flush_success = flush_success
            self.flush_progress = flush_progress
            self.flush_error = flush_error
            #
            # Compact small messages expecially when both headers and
            # body are in memory and hope that the message is so small
            # that takes just a single L2 packet, and so the protocol
            # might be able to suck up the message with just a single
            # recv().
            #
            length = 0
            for x in self.sendqueue:
                if isinstance(x, basestring):
                    length += len(x)
                    continue
                length += file_length(x)
            if length <= 8000:
                data = []
                for x in self.sendqueue:
                    if isinstance(x, basestring):
                        data.append(x)
                        continue
                    data.append(x.read())
                data = "".join(data)
                self.sendqueue.clear()
                self.sendqueue.append(data)
            self._do_flush()
        else:
            if flush_error:
                flush_error()

    def _do_flush(self):
        while True:
            if len(self.sendqueue) == 0:
                notify = self.flush_success
                self.flush_success = None
                self.flush_progress = None
                self.flush_error = None
                if notify:
                    notify()
                return
            x = self.sendqueue[0]
            if isinstance(x, basestring):
                self.sendqueue.popleft()
                self.stream.send(x, self._flush_progress)
                return
            #
            # This used to be 8 KiB, but when reading
            # from a StringIO the transfer was very slow
            # and so I've raised it to 256 KiB, which
            # yields more reasonable speeds.
            #
            data = x.read(262144)
            if not data:
                self.sendqueue.popleft()
                continue
            self.stream.send(data, self._flush_progress)
            return

    def _flush_progress(self, stream, data):
        if self.flush_progress:
            self.flush_progress(data)
        self._do_flush()

    #
    # receive
    #

    def start_receiving(self):
        if not (self.flags & ISCLOSED):
            self.stream.recv(8000, self._got_data)

    def _got_data(self, stream, data):
        self.receiver.progress(data)
        if self.incoming:
            self.incoming.append(data)
            data = "".join(self.incoming)
            del self.incoming[:]
        #
        # The less we bufferize and the faster we are because we
        # don't suffer slowdowns copying data around and we don't
        # cause too much fragmentation.  So, the strategy is that
        # we consume as much as possible of each incoming piece.
        #
        offset = 0
        length = len(data)
        while length > 0:
            #
            # When reading HTTP either you know the length (of the
            # whole body, of a chunk, etc.) or you need to read at
            # least one line (an header, the chunk-lenght, etc).
            #
            if self.left > 0:
                count = min(self.left, length)
                piece = buffer(data, offset, count)
                self.left -= count
                offset += count
                length -= count
                self._got_piece(piece)
            else:
                index = data.find("\n", offset)
                if index == -1:
                    if length > MAXLINE:
                        self.close()
                        return
                    break
                index = index + 1
                line = data[offset:index]
                length -= (index - offset)
                offset = index
                self._got_line(line)
            #
            # Be careful because both _got_piece() and _got_line()
            # might invoke self.close()--this happens for example
            # in case of protocol error.
            #
            if self.flags & ISCLOSED:
                return
        if length > 0:
            remainder = data[offset:]
            self.incoming.append(remainder)
        self.stream.recv(8000, self._got_data)

    #
    # The code below implements a MECHANISM for reading HTTP, but the POLICY
    # decision is demanded to the receiver.  In particular, the callback that
    # is invoked at end-of-headers should return (i) the next state of the
    # reading FSM _and_ (ii) the length of the body (relevant only if the
    # state is either BOUNDED or UNBOUNDED).
    # The current implementation has two minor bugs--the former is that it
    # does not implement MIME folding, and the latter is that it ignores the
    # trailers.
    #
    # TODO Hmm this should probably become part of a separate mixin
    # or class because it's quite a different beast with respect to the
    # code above.
    #

    def _got_line(self, line):
        if self.state == FIRSTLINE:
            vector = line.strip().split(None, 2)
            if len(vector) == 3:
                if line.startswith("HTTP"):
                    protocol, code, reason = vector
                    self.receiver.got_response_line(protocol, code, reason)
                else:
                    method, uri, protocol = vector
                    self.receiver.got_request_line(method, uri, protocol)
                if protocol not in PROTOCOLS:
                    self.close()
                else:
                    self.state = HEADER
            else:
                self.close()
        elif self.state == HEADER:
            if line.strip():
                index = line.find(":")
                if index >= 0:
                    key, value = line.split(":", 1)
                    self.receiver.got_header(key.strip(), value.strip())
                else:
                    self.close()
            else:
                self.state, self.left = self.receiver.end_of_headers()
                if self.state == ERROR:
                    self.close()
        elif self.state == CHUNK_LENGTH:
            vector = line.split()
            if len(vector) >= 1:
                try:
                    length = int(vector[0], 16)
                except ValueError:
                    self.close()
                else:
                    if length < 0:
                        self.close()
                    elif length == 0:
                        self.state = TRAILER
                    else:
                        self.left = length
                        self.state = CHUNK
            else:
                self.close()
        elif self.state == CHUNK_END:
            if line.strip():
                self.close()
            else:
                self.state = CHUNK_LENGTH
        elif self.state == TRAILER:
            if not line.strip():
                self.state = FIRSTLINE
                self.receiver.end_of_body()
            else:
                # Ignoring trailers
                pass
        else:
            log.debug("Not expecting a line")
            self.close()

    def _got_piece(self, piece):
        if self.state == BOUNDED:
            self.receiver.got_piece(piece)
            if self.left == 0:
                self.state = FIRSTLINE
                self.receiver.end_of_body()
        elif self.state == UNBOUNDED:
            self.receiver.got_piece(piece)
            self.left = 8000
        elif self.state == CHUNK:
            self.receiver.got_piece(piece)
            if self.left == 0:
                self.state = CHUNK_END
        else:
            log.debug("Not expecting a piece")
            self.close()
