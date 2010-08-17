# neubot/http/handlers.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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
# Protocol handler
#

import StringIO
import collections
import neubot
import os

# Possible states of the receiver
(IDLE, BOUNDED, UNBOUNDED, CHUNK, CHUNK_END, FIRSTLINE,
 HEADER, CHUNK_LENGTH, TRAILER, ERROR) = range(0,10)

# Accepted HTTP protocols
PROTOCOLS = ["HTTP/1.0", "HTTP/1.1"]

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

    def __init__(self, stream):
        self.stream = stream
        self.stream.notify_closing = self._closing
        self.isclosed = False
        # sending
        self.sendqueue = collections.deque()
        self.flush_success = None
        self.flush_progress = None
        self.flush_error = None
        # receiving
        self.incoming = []
        self.receiver = None
        self.left = 0
        self.state = IDLE

    def __del__(self):
        pass

    def passiveclose(self):
        neubot.net.sched(30, self.close)
        self.state = IDLE

    def close(self, check_eof=False):
        if not self.isclosed:
            self.isclosed = True
            neubot.net.unsched(30, self.close)
            if check_eof and self.stream.eof and self.state == UNBOUNDED:
                self.receiver.end_of_body()
            if self.receiver:
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
    # The code below compacts small messages.  And this is done
    # because we want to pass the socket layer a single buffer
    # that contains the whole message, rather than some few very
    # small buffers (and so the socket layer might send one single
    # small packet instead of two very small packets.)
    # In _do_flush() we read pieces up to 256 KiB from each string-
    # io or file that is appended to our sendqueue.  The value of
    # 256 KiB is a compromise--a small value is not likely to block
    # the read(2) when reading from the disk, but might slow down
    # the transfer speed (between neubot/0.1.2 and neubot/0.1.4 we
    # used 8000 B and that caused *major* slowdowns).  Probably the
    # best solution here is not to rely on "magic" numbers but to
    # use non-blocking I/O for files.
    # For delayed responses where the client has already closed the
    # connection, close() should already have been invoked by the
    # stream code, but the class should be alive because of the ref
    # kept in neubot/notify.py.  And when the notify code invokes
    # bufferize and flushes the senqueue nothing harmful will happen
    # because .isclosed is protecting us.
    # In _do_flush() we don't loop after a successful send because
    # we don't want to delay OTHER writable streams' send().
    #

    def bufferize(self, stringio):
        if not self.isclosed:
            self.sendqueue.append(stringio)

    def flush(self, flush_success, flush_progress=None, flush_error=None):
        if not self.isclosed:
            self.flush_success = flush_success
            self.flush_progress = flush_progress
            self.flush_error = flush_error
            length = 0
            for stringio in self.sendqueue:
                stringio.seek(0, os.SEEK_END)
                length += stringio.tell()
                stringio.seek(0, os.SEEK_SET)
            if length <= 8000:
                data = []
                for stringio in self.sendqueue:
                    data.append(stringio.read())
                data = "".join(data)
                stringio = StringIO.StringIO(data)
                self.sendqueue.clear()
                self.sendqueue.append(stringio)
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
                break
            stringio = self.sendqueue[0]
            data = stringio.read(262144)
            if not data:
                self.sendqueue.popleft()
                continue
            self.stream.send(data, self._flush_progress)
            break

    def _flush_progress(self, stream, data):
        if self.flush_progress:
            self.flush_progress(data)
        self._do_flush()

    #
    # The more we bufferize the slower we are--and so try to consume
    # as much as possible of each incoming piece of data.
    # By default we read line-by-line, unless we know the size of the
    # next body piece--and that's exactly how HTTP works from a low
    # abstraction level's perspective: you read headers (a sequence of
    # lines) and then you decide the body length (either via content-
    # length or reading the chunk-length, which is another line), and
    # at this point you know the length of the next piece, you read it,
    # and so forth.
    # In case of protocol error the higher layers will invoke close()
    # and so we must check .isclosed after each iteration in the loop
    # that processes incoming data.
    #

    def attach(self, receiver):
        self.receiver = receiver
        self.state = FIRSTLINE
        self.stream.recv(8000, self._got_data)

    def _got_data(self, stream, data):
        self.receiver.progress(data)
        if self.incoming:
            self.incoming.append(data)
            data = "".join(self.incoming)
            del self.incoming[:]
        offset = 0
        length = len(data)
        while length > 0:
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
                    break
                index = index + 1
                line = data[offset:index]
                length -= (index - offset)
                offset = index
                self._got_line(line)
            if self.isclosed:
                break
        if length > 0:
            remainder = data[offset:]
            self.incoming.append(remainder)
        if not self.isclosed:
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

    def _got_line(self, line):
        if self.state == FIRSTLINE:
            vector = line.split()
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
            neubot.log.debug("Not expecting a line")
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
            neubot.log.debug("Not expecting a piece")
            self.close()
