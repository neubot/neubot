# neubot/http_clnt.py

#
# Copyright (c) 2011-2012
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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

''' HTTP client '''

# Adapted from neubot/http/stream.py
# Python3-ready: yes

import collections
import getopt
import logging
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.buff import Buff
from neubot.handler import Handler
from neubot.poller import POLLER
from neubot.stream import Stream

from neubot import six
from neubot import utils_version

MAXLINE = 512
MAXPIECE = 524288
MAXREAD = 8000
MAXRECEIVE = 262144

CHARSET = six.b('charset')
CHUNKED = six.b('chunked')
CLOSE = six.b('close')
CODE204 = six.b('204')
CODE304 = six.b('304')
COLON = six.b(':')
COMMASPACE = six.b(', ')
CONNECTION = six.b('connection')
CONTENT_LENGTH = six.b('content-length')
CONTENT_TYPE = six.b('content-type')
CRLF = six.b('\r\n')
EMPTY_STRING = six.b('')
EQUAL = six.b('=')
HEAD = six.b('HEAD')
HTTP_PREFIX = six.b('HTTP/')
HTTP10 = six.b('HTTP/1.0')
HTTP11 = six.b('HTTP/1.1')
LAST_CHUNK = six.b('0\r\n')
ONE = six.b('1')
SEMICOLON = six.b(';')
SPACE = six.b(' ')
TAB = six.b('\t')
TRANSFER_ENCODING = six.b('transfer-encoding')

LOGGER = logging.getLogger('http_clnt')

class HttpClientContext(Buff):

    ''' HTTP client context '''

    def __init__(self, extra, connection_made, connection_lost):
        Buff.__init__(self)
        self.code = EMPTY_STRING
        self.connection_made = connection_made
        self.connection_lost = connection_lost
        self.extra = extra
        self.handle_input = None
        self.headers = {}
        self.last_hdr = EMPTY_STRING
        self.left = 0
        self.max_headers = 0
        self.method = EMPTY_STRING
        self.outfp = None
        self.outfp_chunked = False
        self.outq = []
        self.protocol = EMPTY_STRING
        self.reason = EMPTY_STRING

class HttpClient(Handler):

    ''' HTTP client '''

    #
    # Setup.  The user should implement handle_connect() and invoke
    # create_stream().  This function setups a new stream and asks
    # the poller to register the stream as readable.  In turn, this
    # is imperative to avoid delaying EOF and RST.
    #

    def create_stream(self, sock, connection_made, connection_lost,
                      sslconfig, sslcert, extra):
        ''' Creates an HTTP stream '''
        LOGGER.debug('stream setup... in progress')
        context = HttpClientContext(extra, connection_made, connection_lost)
        Stream(sock, self._handle_connection_made, self._handle_connection_lost,
               sslconfig, sslcert, context)

    def _handle_connection_made(self, stream):
        ''' Internally handles the CONNECTION_MADE event '''
        context = stream.opaque
        context.handle_input = self._handle_firstline
        stream.recv(MAXRECEIVE, self._handle_data)
        if context.connection_made:
            context.connection_made(stream)
        LOGGER.debug('stream setup... complete')

    def _handle_connection_lost(self, stream):
        ''' Internally handles the CONNECTION_LOST event '''
        context = stream.opaque
        if stream.eof and context.handle_input == self._handle_piece_unbounded:
            LOGGER.debug('EOF terminates unbounded body')
            # There may be bufferised data
            piece = context.getvalue()
            if piece:
                context.handle_input(stream, piece)
            self._handle_end_of_body(stream)
        if context.connection_lost:
            context.connection_lost(stream)

    #
    # Send path.  This section has methods to append headers and body to the
    # internal output buffer.  Once the HTTP message is ready, send_message()
    # allows the programmer to start sending it.  When the message is sent,
    # handle_send_complete() is invoked.  This is an empty method that can be
    # overriden to take actions.
    #

    @staticmethod
    def append_request(stream, method, uri, protocol):
        ''' Append request to output buffer '''
        context = stream.opaque
        LOGGER.debug('> %s %s %s', method, uri, protocol)
        context.method = six.b(method)  # Save for _handle_end_of_headers()
        context.outq.append(six.b(method))
        context.outq.append(SPACE)
        context.outq.append(six.b(uri))
        context.outq.append(SPACE)
        context.outq.append(six.b(protocol))
        context.outq.append(CRLF)

    @staticmethod
    def append_header(stream, name, value):
        ''' Append header to output buffer '''
        context = stream.opaque
        LOGGER.debug('> %s: %s', name, value)
        context.outq.append(six.b(name))
        context.outq.append(COLON)
        context.outq.append(SPACE)
        context.outq.append(six.b(value))
        context.outq.append(CRLF)

    @staticmethod
    def append_end_of_headers(stream):
        ''' Append end-of-headers (an empty line) to output buffer '''
        context = stream.opaque
        LOGGER.debug('>')
        context.outq.append(CRLF)

    @staticmethod
    def append_bytes(stream, bytez):
        ''' Append bytes to output buffer '''
        context = stream.opaque
        context.outq.append(bytez)

    @staticmethod
    def append_chunk(stream, bytez):
        ''' Append chunk to output buffer '''
        context = stream.opaque
        LOGGER.debug('> {chunk len=%d}', len(bytez))
        context.outq.append(six.b('%x\r\n' % len(bytez)))
        context.outq.append(bytez)
        context.outq.append(CRLF)

    @staticmethod
    def append_last_chunk(stream):
        ''' Append last-chunk to output buffer '''
        context = stream.opaque
        LOGGER.debug('> {last-chunk}')
        context.outq.append(LAST_CHUNK)

    @staticmethod
    def append_file(stream, filep, chunked=False):
        ''' Append file to output buffer '''
        context = stream.opaque
        if not chunked:
            LOGGER.debug('> {file}')
        context.outfp = filep
        context.outfp_chunked = chunked

    def send_message(self, stream):
        ''' Send output buffer content to the other end '''
        context = stream.opaque
        string = EMPTY_STRING.join(context.outq)
        context.outq = []
        stream.send(string, self._handle_send_complete)

    def _handle_send_complete(self, stream):
        ''' Internally handles the SEND_COMPLETE event '''
        context = stream.opaque
        if context.outfp:
            bytez = context.outfp.read(MAXREAD)
            if bytez:
                if context.outfp_chunked:
                    self.append_chunk(stream, bytez)
                    self.send_message(stream)
                else:
                    stream.send(bytez, self._handle_send_complete)
                return
            if context.outfp_chunked:
                context.outfp_chunked = False
                context.outfp = None
                self.append_last_chunk(stream)
                # Note: no support for trailers
                self.append_end_of_headers(stream)
                self.send_message(stream)
                return
            context.outfp_chunked = False
            context.outfp = None
        self.handle_send_complete(stream)

    def handle_send_complete(self, stream):
        ''' Handles the SEND_COMPLETE event '''

    #
    # Receive path.  The receiver automatically receives HTTP messages and
    # dispatches events accordingly.  Handle_end_of_headers() is invoked after
    # headers are received.  Handle_body_piece() is invoked for each received
    # body piece.  Handle_end_of_body() is invoked when the whole message
    # has been received.
    #   The code does not check whether a response is expected or not, leaving
    # the decision to the programmer.  It is designed like this to allow the
    # programmer to receive interim responses like '100 Continue'.
    #

    def _handle_data(self, stream, bytez):
        ''' Handles the DATA event '''
        context = stream.opaque
        context.bufferise(bytez)
        while True:
            if context.left > 0:
                tmp = context.pullup(min(context.left, MAXRECEIVE))
                if not tmp:
                    break
                context.left -= len(tmp)  # MUST be before handle_input()
                if context.left < 0:
                    raise RuntimeError('negative context.left')
            elif context.left == 0:
                tmp = context.getline(MAXLINE)
                if not tmp:
                    break
            else:
                raise RuntimeError('negative context.left')
            context.handle_input(stream, tmp)
        if not stream.isclosed:
            stream.recv(MAXRECEIVE, self._handle_data)

    def _handle_firstline(self, stream, line):
        ''' Handles the FIRSTLINE event '''
        context = stream.opaque
        line = line.rstrip()
        LOGGER.debug('< %s', six.bytes_to_string_safe(line, 'utf-8'))
        vector = line.split(None, 2)
        if len(vector) != 3:
            raise RuntimeError('invalid first line')
        context.protocol = vector[0]
        context.code = vector[1]
        context.reason = vector[2]
        if not context.protocol.startswith(HTTP_PREFIX):
            raise RuntimeError('invalid protocol')
        if context.protocol not in (HTTP11, HTTP10):
            raise RuntimeError('unsupported protocol')
        context.last_hdr = EMPTY_STRING
        context.headers = {}
        context.max_headers = 128  # include also trailers
        context.handle_input = self._handle_header

    def _handle_header(self, stream, line):
        ''' Handles the HEADER event '''
        self._handle_header_ex(stream, line, self._handle_end_of_headers)

    @staticmethod
    def _handle_header_ex(stream, line, handle_done):
        ''' Handles the HEADER_EX event '''
        context = stream.opaque
        context.max_headers -= 1
        if context.max_headers <= 0:
            raise RuntimeError('too many headers')
        line = line.rstrip()
        if not line:
            LOGGER.debug('<')
            handle_done(stream)
            return
        LOGGER.debug('< %s', six.bytes_to_string_safe(line, 'utf-8'))
        # Note: must preceed header parsing to permit colons in folded line(s)
        if context.last_hdr and line[0:1] in (SPACE, TAB):
            value = context.headers[context.last_hdr]
            value += SPACE
            value += line.strip()
            # Note: make sure there are no leading or trailing spaces
            context.headers[context.last_hdr] = value.strip()
            return
        index = line.find(COLON)
        if index >= 0:
            name, value = line.split(COLON, 1)
            # Note: header names are case insensitive
            name = name.strip().lower()
            value = value.strip()
            if name not in context.headers:
                context.headers[name] = value
            else:
                context.headers[name] += COMMASPACE
                context.headers[name] += value
            context.last_hdr = name
            return
        raise RuntimeError('invalid header')

    def _handle_end_of_headers(self, stream):
        ''' Internally handles the END_OF_HEADERS event '''

        #
        #     "[...] All responses to the HEAD request method MUST NOT include a
        # message-body, even though the presence of entity-header fields might
        # lead one to believe they do. All 1xx (informational), 204 (no content)
        # and 304 (not modified) responses MUST NOT include a message-body.  All
        # other responses do include a message-body, although it MAY be of zero
        # length."  (RFC2616, sect. 4.3)
        #

        context = stream.opaque

        # Note: context.code[0:1] is for Python3 compat
        if (context.method == HEAD or context.code[0:1] == ONE or
          context.code == CODE204 or context.code == CODE304):
            LOGGER.debug('no message body')
            self.handle_end_of_headers(stream)
            context.handle_input = self._handle_firstline  # Robustness
            # Note: pretend there was an empty body
            self._handle_end_of_body(stream)
            return

        # Note: chunked has precedence over content-length
        if context.headers.get(TRANSFER_ENCODING) == CHUNKED:
            LOGGER.debug('chunked message body')
            context.handle_input = self._handle_chunklen
            self.handle_end_of_headers(stream)
            return

        tmp = context.headers.get(CONTENT_LENGTH)
        if tmp:
            length = int(tmp)
            if length > 0:
                LOGGER.debug('bounded message body')
                context.handle_input = self._handle_piece_bounded
                context.left = length
                self.handle_end_of_headers(stream)
                return
            if length == 0:
                LOGGER.debug('empty message body')
                self.handle_end_of_headers(stream)
                context.handle_input = self._handle_firstline  # Robustness
                self._handle_end_of_body(stream)
                return
            raise RuntimeError('negative content length')

        LOGGER.debug('unbounded message body')
        context.handle_input = self._handle_piece_unbounded
        context.left = MAXPIECE
        self.handle_end_of_headers(stream)

    def _handle_chunklen(self, stream, line):
        ''' Handles the CHUNKLEN event '''
        context = stream.opaque
        vector = line.split()
        if vector:
            length = int(vector[0], 16)
            if length > 0:
                context.left = length
                context.handle_input = self._handle_piece_chunked
                LOGGER.debug('< {chunk len=%d}', length)
            elif length == 0:
                context.handle_input = self._handle_trailer
                LOGGER.debug('< {last-chunk/}')
            else:
                raise RuntimeError('negative chunk-length')
        else:
            raise RuntimeError('bad chunk-length line')

    def _handle_chunkend(self, stream, line):
        ''' Handles the CHUNKEND event '''
        context = stream.opaque
        if not line.strip():
            LOGGER.debug('< {/chunk}')
            context.handle_input = self._handle_chunklen
        else:
            raise RuntimeError('bad chunk-end line')

    def _handle_trailer(self, stream, line):
        ''' Handles the TRAILER event '''
        self._handle_header_ex(stream, line, self._handle_end_of_body)

    def _handle_piece_unbounded(self, stream, piece):
        ''' Handles the PIECE_UNBOUNDED event '''
        context = stream.opaque
        self.handle_body_piece(stream, piece)
        context.left = MAXPIECE  # Read until the connection is closed

    def _handle_piece_bounded(self, stream, piece):
        ''' Handles the PIECE_BOUNDED event '''
        context = stream.opaque
        self.handle_body_piece(stream, piece)
        if context.left == 0:
            self._handle_end_of_body(stream)

    def _handle_piece_chunked(self, stream, piece):
        ''' Handles the PIECE_CHUNKED event '''
        context = stream.opaque
        self.handle_body_piece(stream, piece)
        if context.left == 0:
            context.handle_input = self._handle_chunkend

    def _handle_end_of_body(self, stream):
        ''' Internally handles the END_OF_BODY event '''
        #
        # It is user responsibility to close the stream if appropriate (i.e.
        # if HTTP/1.0 or if "Connection" is set to "close").
        #
        context = stream.opaque
        context.handle_input = self._handle_firstline  # Restart
        self.handle_end_of_body(stream)

    def handle_end_of_headers(self, stream):
        ''' Handles the END_OF_HEADERS event '''

    def handle_body_piece(self, stream, piece):
        ''' Handles the BODY_PIECE event '''

    def handle_end_of_body(self, stream):
        ''' Handles the END_OF_BODY event '''

class HttpClientSmpl(HttpClient):
    ''' Simple HTTP client '''

    def handle_connect(self, connector, sock, rtt, sslconfig, extra):
        self.create_stream(sock, self._connection_made, None,
                           sslconfig, None, extra)

    def _connection_made(self, stream):
        ''' Invoked when the connection is established '''
        context = stream.opaque
        address, port, paths, cntvec, close = context.extra[:5]
        if not paths:
            stream.close()
            return
        self.append_request(stream, 'GET', paths.popleft(), 'HTTP/1.1')
        self.append_header(stream, 'Host', '%s:%s' % (address, port))
        self.append_header(stream, 'User-Agent', utils_version.HTTP_HEADER)
        self.append_header(stream, 'Cache-Control', 'no-cache')
        self.append_header(stream, 'Pragma', 'no-cache')
        #
        # GET http://mlab-ns.appspot.com/neubot returns a chunked response if
        # the client does not send 'Connection: close'.  Otherwise the response
        # is up to EOF.  Also http://www.google.it/ seems to behave the same
        # way.  Therefore, the close knob allows to test the client compliancy
        # in light of this behavior.
        #
        if close:
            self.append_header(stream, 'Connection', 'close')
        self.append_end_of_headers(stream)
        self.send_message(stream)
        cntvec[0] += 1

    def handle_end_of_headers(self, stream):
        context = stream.opaque
        encoding = context.extra[5]
        value = context.headers.get(CONTENT_TYPE)
        if not value:
            return
        # type"/"subtype *( ";"parameter )
        index = value.find(SEMICOLON)
        if index < 0:
            return
        value = value[index + 1:]
        tokens = value.split(SEMICOLON)
        for token in tokens:
            index = token.find(EQUAL)
            if index < 0:
                continue
            name = token[:index].strip().lower()
            value = token[index + 1:].strip()
            if name == CHARSET:
                encoding[0] = six.bytes_to_string_safe(value, 'ascii')
                LOGGER.debug('response encoding: %s', encoding[0])

    def handle_end_of_body(self, stream):
        context = stream.opaque
        cntvec = context.extra[3]
        if cntvec[0] <= 0:  # No unexpected responses
            raise RuntimeError('http_dload: unexpected response')
        cntvec[0] -= 1
        sys.stdout.flush()
        # Ignoring the "Connection" header for HTTP/1.0
        if (context.protocol == HTTP10 or
          context.headers.get(CONNECTION) == CLOSE):
            stream.close()
            return
        self._connection_made(stream)

    def handle_body_piece(self, stream, data):
        # Remember that with Python 3 we need to decode data
        context = stream.opaque
        encoding = context.extra[5]
        data = six.bytes_to_string(data, encoding[0])
        sys.stdout.write(data)

USAGE = 'usage: neubot http_clnt [-6CSv] [-A address] [-p port] path...'

def main(args):
    ''' Main function '''

    try:
        options, arguments = getopt.getopt(args[1:], '6A:Cp:Sv')
    except getopt.error:
        sys.exit(USAGE)
    if not arguments:
        sys.exit(USAGE)

    prefer_ipv6 = 0
    address = '127.0.0.1'
    close = 0
    port = 80
    sslconfig = 0
    level = logging.INFO
    for name, value in options:
        if name == '-6':
            prefer_ipv6 = 1
        elif name == '-A':
            address = value
        elif name == '-C':
            close = 1
        elif name == '-p':
            port = int(value)
        elif name == '-S':
            sslconfig = 1
        elif name == '-v':
            level = logging.DEBUG

    logging.getLogger().setLevel(level)

    handler = HttpClientSmpl()
    handler.connect((address, port), prefer_ipv6, sslconfig,
      (address, port, collections.deque(arguments), [0], close,
       ['utf-8']))
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
