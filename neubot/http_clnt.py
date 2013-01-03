# neubot/http_clnt.py

#
# Copyright (c) 2011-2012 Simone Basso <bassosimone@gmail.com>,
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

''' HTTP client '''

# Adapted from neubot/http/stream.py
# Python3-ready: yes

import collections
import getopt
import logging
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.brigade import Brigade
from neubot.handler import Handler
from neubot.poller import POLLER
from neubot.stream import Stream

from neubot import six
from neubot import utils_version

MAXLINE = 512
MAXPIECE = 524288
MAXREAD = 8000
MAXRECEIVE = 262144

CHUNKED = six.b('chunked')
CLOSE = six.b('close')
CODE204 = six.b('204')
CODE304 = six.b('304')
COLON = six.b(':')
COMMASPACE = six.b(', ')
CONNECTION = six.b('connection')
CONTENT_LENGTH = six.b('content-length')
CRLF = six.b('\r\n')
EMPTY_STRING = six.b('')
HEAD = six.b('HEAD')
HTTP_PREFIX = six.b('HTTP/')
HTTP10 = six.b('HTTP/1.0')
HTTP11 = six.b('HTTP/1.1')
LAST_CHUNK = six.b('0\r\n')
ONE = six.b('1')
SPACE = six.b(' ')
TAB = six.b('\t')
TRANSFER_ENCODING = six.b('transfer-encoding')

class ClientContext(Brigade):

    ''' HTTP client context '''

    def __init__(self, extra, connection_made, connection_lost):
        Brigade.__init__(self)

        self.outq = []
        self.outfp = None

        self.method = EMPTY_STRING

        self.protocol = EMPTY_STRING
        self.code = EMPTY_STRING
        self.reason = EMPTY_STRING
        self.headers = {}
        self.last_hdr = EMPTY_STRING
        self.body = None

        self.handle_piece = None
        self.handle_line = None
        self.left = 0

        self.extra = extra
        self.connection_made = connection_made
        self.connection_lost = connection_lost

class HttpClient(Handler):

    ''' HTTP client '''

    #
    # Setup.  The user should implement handle_connect() and invoke the
    # create_stream() function to setup a new stream.  Stream creation is
    # wrapped by a function because the HTTP code must kick off the HTTP
    # receiver once the connection is ready.  Indeed, the receiver is "ON"
    # during the whole connection lifetime, so that EOF and RST can be
    # detected immediately (the underlying socket is in select() read set
    # as long as the HTTP code keeps receiving).
    #

    def create_stream(self, sock, connection_made, connection_lost,
          sslconfig, sslcert, extra):
        ''' Creates an HTTP stream '''
        logging.debug('http_clnt: stream setup... in progress')
        context = ClientContext(extra, connection_made, connection_lost)
        Stream(sock, self._handle_connection_made, self._handle_connection_lost,
          sslconfig, sslcert, context)

    def _handle_connection_made(self, stream):
        ''' Internally handles the CONNECTION_MADE event '''
        context = stream.opaque
        stream.recv(MAXRECEIVE, self._handle_data)  # Kick receiver off
        context.handle_line = self._handle_firstline
        logging.debug('http_clnt: stream setup... complete')
        context.connection_made(stream)

    @staticmethod
    def _handle_connection_lost(stream):
        ''' Internally handles the CONNECTION_LOST event '''
        context = stream.opaque
        if context.connection_lost:
            context.connection_lost(stream)

    #
    # Send path.  This section provides methods to append stuff to the internal
    # output buffer, including an open file handle.  The user is expected to
    # append everything needed to make an HTTP message, and, once that is done,
    # he/she is expected to invoke the send_message() to start sending the whole
    # message to the other end.  Once done, the handle_send_complete() function
    # is invoked (this is an empty method that the user may want to override.)
    #

    @staticmethod
    def append_request(stream, method, uri, protocol):
        ''' Append request to output buffer '''
        context = stream.opaque
        logging.debug('> %s %s %s', method, uri, protocol)
        context.method = six.b(method)
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
        logging.debug('> %s: %s', name, value)
        context.outq.append(six.b(name))
        context.outq.append(COLON)
        context.outq.append(SPACE)
        context.outq.append(six.b(value))
        context.outq.append(CRLF)

    @staticmethod
    def append_end_of_headers(stream):
        ''' Append end-of-headers (an empty line) to output buffer '''
        context = stream.opaque
        logging.debug('>')
        context.outq.append(CRLF)

    @staticmethod
    def append_string(stream, string):
        ''' Append string to output buffer '''
        context = stream.opaque
        context.outq.append(six.b(string))

    @staticmethod
    def append_bytes(stream, bytez):
        ''' Append bytes to output buffer '''
        context = stream.opaque
        context.outq.append(bytez)

    @staticmethod
    def append_chunk(stream, bytez):
        ''' Append chunk to output buffer '''
        context = stream.opaque
        logging.debug('> {chunk len=%d}', len(bytez))
        context.outq.append(six.b('%x\r\n' % len(bytez)))
        context.outq.append(bytez)
        context.outq.append(CRLF)

    @staticmethod
    def append_last_chunk(stream):
        ''' Append last-chunk to output buffer '''
        context = stream.opaque
        logging.debug('> {last-chunk}')
        context.outq.append(LAST_CHUNK)

    @staticmethod
    def append_file(stream, filep):
        ''' Append file to output buffer '''
        context = stream.opaque
        logging.debug('> {file}')
        context.outfp = filep

    def send_message(self, stream):
        ''' Send output buffer content to the other end '''
        context = stream.opaque
        string = EMPTY_STRING.join(context.outq)
        stream.send(string, self._handle_send_complete)
        context.outq = []

    def _handle_send_complete(self, stream):
        ''' Internally handles the SEND_COMPLETE event '''
        context = stream.opaque
        if context.outfp:
            bytez = context.outfp.read(MAXREAD)
            if bytez:
                # Note: honor the queue, don't send directly
                context.outq.append(bytez)
                self.send_message(stream)
                return
            context.outfp = None
        self.handle_send_complete(stream)

    def handle_send_complete(self, stream):
        ''' Handles the SEND_COMPLETE event '''

    #
    # Receive path.  The receiver is always active and the user is expected to
    # handle the end of headers and end of body events, by overriding the
    # corresponding functions.  One caveat: the decision whether a response
    # is expected or not is left to the user (typically you expect a response
    # after a full request was sent, but there are exceptions, e.g. the "100
    # Continue" case).  Also, it should be noted that, by default, response
    # body is discarded: the user is expected to override context.body and
    # point it to a file-like object, if he/she wants to save it.
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
                context.left -= len(tmp)  # MUST be before got_piece()
                context.handle_piece(stream, tmp)
            elif context.left == 0:
                tmp = context.getline(MAXLINE)
                if not tmp:
                    break
                context.handle_line(stream, tmp)
            else:
                raise RuntimeError('negative context.left')
        if not stream.isclosed:
            stream.recv(MAXRECEIVE, self._handle_data)

    def _handle_firstline(self, stream, line):
        ''' Handles the FIRSTLINE event '''
        context = stream.opaque
        line = line.rstrip()
        logging.debug('< %s', six.bytes_to_string_safe(line, 'utf-8'))
        vector = line.split(None, 2)
        if len(vector) != 3:
            raise RuntimeError('http_clnt: invalid first line')
        context.protocol = vector[0]
        if not context.protocol.startswith(HTTP_PREFIX):
            raise RuntimeError('http_clnt: invalid protocol')
        if context.protocol not in (HTTP11, HTTP10):
            raise RuntimeError('http_clnt: unsuppored protocol')
        context.code = vector[1]
        context.reason = vector[2]
        context.last_hdr = EMPTY_STRING
        context.headers = {}
        context.handle_line = self._handle_header

    def _handle_header(self, stream, line):
        ''' Handles the HEADER event '''
        self._handle_header_ex(stream, line, self.handle_end_of_headers)

    @staticmethod
    def _handle_header_ex(stream, line, handle_done):
        ''' Handles the HEADER_EX event '''
        context = stream.opaque
        line = line.rstrip()
        if not line:
            logging.debug('<')
            handle_done(stream)
            return
        logging.debug('< %s', six.bytes_to_string_safe(line, 'utf-8'))
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
            name = name.strip().lower()
            value = value.strip()
            if name not in context.headers:
                context.headers[name] = value
            else:
                #
                # "Multiple message-header fields with the same field-name MAY
                # be present in a message if and only if the entire field-value
                # for that header field is defined as a comma-separated list
                # [i.e., #(values)]. It MUST be possible to combine the multiple
                # header fields into one "field-name: field-value" pair, without
                # changing the semantics of the message, by appending each
                # subsequent field-value to the first, each separated by
                # a comma."  (RFC2616, sect. 4.2)
                #
                context.headers[name] += COMMASPACE
                context.headers[name] += value
            context.last_hdr = name
            return
        #
        # N.B. I have observed that this error is often triggered when one
        # overrides handle_end_of_body() and forgets to invoke the parent class
        # method, which resets the line reader.
        #
        raise RuntimeError('http_clnt: internal error #2')

    def handle_end_of_headers(self, stream):
        ''' Handle END_OF_HEADERS event '''

        #
        #     "[...] All responses to the HEAD request method MUST NOT include a
        # message-body, even though the presence of entity-header fields might
        # lead one to believe they do. All 1xx (informational), 204 (no content)
        # and 304 (not modified) responses MUST NOT include a message-body.  All
        # other responses do include a message-body, although it MAY be of zero
        # length."  (RFC2616, sect. 4.3)
        #

        context = stream.opaque

        if (context.method == HEAD or context.code[0:1] == ONE or
          context.code == CODE204 or context.code == CODE304):
            logging.debug('http_clnt: expecting no message body')
            self.handle_end_of_body(stream)
            return

        if context.headers.get(TRANSFER_ENCODING) == CHUNKED:
            logging.debug('http_clnt: expecting chunked message body')
            context.handle_line = self._handle_chunklen
            return

        tmp = context.headers.get(CONTENT_LENGTH)
        if tmp:
            length = int(tmp)
            if length > 0:
                logging.debug('http_clnt: expecting bounded message body')
                context.handle_piece = self._handle_piece_bounded
                context.left = length
                return
            if length == 0:
                logging.debug('http_clnt: expecting no message body')
                self.handle_end_of_body(stream)
                return
            raise RuntimeError('http_clnt: invalid content length')

        logging.debug('http_clnt: expecting unbounded message body')
        context.handle_piece = self._handle_piece_unbounded
        context.left = MAXPIECE

    def _handle_chunklen(self, stream, line):
        ''' Handles the CHUNKLEN event '''
        context = stream.opaque
        vector = line.split()
        if vector:
            tmp = int(vector[0], 16)
            if tmp < 0:
                raise RuntimeError('http_clnt: negative chunk-length')
            elif tmp == 0:
                context.handle_line = self._handle_trailer
                logging.debug('< {last-chunk/}')
            else:
                context.left = tmp
                context.handle_piece = self._handle_piece_chunked
                logging.debug('< {chunk len=%d}', tmp)
        else:
            raise RuntimeError('http_clnt: bad chunk-length line')

    def _handle_chunkend(self, stream, line):
        ''' Handles the CHUNKEND event '''
        context = stream.opaque
        if not line.strip():
            logging.debug('< {/chunk}')
            context.handle_line = self._handle_chunklen
        else:
            raise RuntimeError('http_clnt: bad chunk-end line')

    def _handle_trailer(self, stream, line):
        ''' Handles the TRAILER event '''
        self._handle_header_ex(stream, line, self.handle_end_of_body)

    def _handle_piece_unbounded(self, stream, piece):
        ''' Handles the PIECE_UNBOUNDED event '''
        context = stream.opaque
        self.handle_piece(stream, piece)
        context.left = MAXPIECE  # Read until the connection is closed

    def _handle_piece_bounded(self, stream, piece):
        ''' Handles the PIECE_BOUNDED event '''
        context = stream.opaque
        self.handle_piece(stream, piece)
        if context.left == 0:
            self.handle_end_of_body(stream)

    def _handle_piece_chunked(self, stream, piece):
        ''' Handles the PIECE_CHUNKED event '''
        context = stream.opaque
        self.handle_piece(stream, piece)
        if context.left == 0:
            context.handle_line = self._handle_chunkend

    @staticmethod
    def handle_piece(stream, piece):
        ''' Handle the PIECE event '''
        # Note: by default the body is discarded
        context = stream.opaque
        if context.body:
            context.body.write(piece)

    def handle_end_of_body(self, stream):
        ''' Handle the END_OF_BODY event '''
        #
        # It is user responsibility to close the stream here
        # if appropriate (i.e. if HTTP/1.0 or if the "Connection"
        # header value is set to  "close").
        #
        context = stream.opaque
        context.handle_line = self._handle_firstline  # Restart

class HttpClientSmpl(HttpClient):
    ''' Simple HTTP client '''

    def handle_connect(self, connector, sock, rtt, sslconfig, extra):
        self.create_stream(sock, self.connection_made, None,
          sslconfig, None, extra)

    def connection_made(self, stream):
        ''' Invoked when the connection is established '''
        context = stream.opaque
        address, port, paths, cntvec = context.extra
        if not paths:
            stream.close()
            return
        self.append_request(stream, 'GET', paths.popleft(), 'HTTP/1.1')
        self.append_header(stream, 'Host', '%s:%s' % (address, port))
        self.append_header(stream, 'User-Agent', utils_version.HTTP_HEADER)
        self.append_header(stream, 'Cache-Control', 'no-cache')
        self.append_header(stream, 'Pragma', 'no-cache')
        self.append_end_of_headers(stream)
        self.send_message(stream)
        context.body = self  # Want to print the body
        cntvec[0] += 1

    def handle_end_of_body(self, stream):
        HttpClient.handle_end_of_body(self, stream)
        context = stream.opaque
        cntvec = context.extra[3]
        if cntvec[0] <= 0:  # No unexpected responses
            raise RuntimeError('http_dload: unexpected response')
        cntvec[0] -= 1
        sys.stdout.flush()
        # XXX ignoring the "Connection" header for HTTP/1.0
        if (context.protocol == HTTP10 or
          context.headers.get(CONNECTION) == CLOSE):
            stream.close()
            return
        self.connection_made(stream)

    def write(self, data):
        ''' Write data on standard output '''
        # Remember that with Python 3 we need to decode data
        sys.stdout.write(six.bytes_to_string(data, 'utf-8'))

USAGE = 'usage: neubot http_clnt [-6Sv] [-A address] [-p port] path...'

def main(args):
    ''' Main function '''

    try:
        options, arguments = getopt.getopt(args[1:], '6A:p:Sv')
    except getopt.error:
        sys.exit(USAGE)
    if not arguments:
        sys.exit(USAGE)

    prefer_ipv6 = 0
    address = '127.0.0.1'
    sslconfig = 0
    port = 80
    level = logging.INFO
    for name, value in options:
        if name == '-6':
            prefer_ipv6 = 1
        elif name == '-A':
            address = value
        elif name == '-p':
            port = int(value)
        elif name == '-S':
            sslconfig = 1
        elif name == '-v':
            level = logging.DEBUG

    logging.getLogger().setLevel(level)

    handler = HttpClientSmpl()
    handler.connect((address, port), prefer_ipv6, sslconfig,
      (address, port, collections.deque(arguments), [0]))
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
