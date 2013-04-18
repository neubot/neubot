#!/usr/bin/env python

#
# Copyright (c) 2012
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

''' Regression tests for neubot/http_clnt.py '''

#
# Regress-for: neubot/http_clnt.py
# Python3-ready: yes 
#

import unittest
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import http_clnt
from neubot import six

class FakeStream(object):
    ''' Fakes out a real stream '''

    # This class implements a simplified Stream object that just exposes
    # the methods and attributes required by this file.

    def __init__(self, context):
        self.opaque = context
        self.outs = http_clnt.EMPTY_STRING
        self.count = 0
        self.func = None
        self.isclosed = 0

    def send(self, data, func):
        ''' Emulates stream send() '''
        self.outs = data
        # func is ignored

    def recv(self, count, func):
        ''' Emulates stream recv() '''
        self.count = count
        self.func = func

class PrepareMessage(unittest.TestCase):
    ''' Regression test for code that prepares a message '''

    def test_append_request(self):
        ''' Make sure append_request() works '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        client.append_request(stream, 'GET', '/', 'HTTP/1.0')
        self.assertEqual(context.method, six.b('GET'))
        self.assertEqual(context.outq[0], six.b('GET'))
        self.assertEqual(context.outq[1], http_clnt.SPACE)
        self.assertEqual(context.outq[2], six.b('/'))
        self.assertEqual(context.outq[3], http_clnt.SPACE)
        self.assertEqual(context.outq[4], six.b('HTTP/1.0'))
        self.assertEqual(context.outq[5], http_clnt.CRLF)
        self.assertEqual(len(context.outq), 6)

    def test_append_header(self):
        ''' Make sure append_header() works '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        client.append_header(stream, 'Content-Type', 'text/plain')
        self.assertEqual(context.outq[0], six.b('Content-Type'))
        self.assertEqual(context.outq[1], http_clnt.COLON)
        self.assertEqual(context.outq[2], http_clnt.SPACE)
        self.assertEqual(context.outq[3], six.b('text/plain'))
        self.assertEqual(context.outq[4], http_clnt.CRLF)
        self.assertEqual(len(context.outq), 5)

    def test_append_end_of_headers(self):
        ''' Make sure append_end_of_headers() works '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        client.append_end_of_headers(stream)
        self.assertEqual(context.outq[0], http_clnt.CRLF)
        self.assertEqual(len(context.outq), 1)

    def test_append_string(self):
        ''' Make sure append_string() works '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        client.append_string(stream, 'A' * 512)
        self.assertEqual(context.outq[0], six.b('A') * 512)
        self.assertEqual(len(context.outq), 1)

    def test_append_bytes(self):
        ''' Make sure append_bytes() works '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        client.append_bytes(stream, six.b('A') * 512)
        self.assertEqual(context.outq[0], six.b('A') * 512)
        self.assertEqual(len(context.outq), 1)

    def test_append_chunk(self):
        ''' Make sure append_chunk() works '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        client.append_chunk(stream, six.b('A') * 513)
        self.assertEqual(context.outq[0], six.b('201\r\n'))
        self.assertEqual(context.outq[1], six.b('A') * 513)
        self.assertEqual(context.outq[2], http_clnt.CRLF)
        self.assertEqual(len(context.outq), 3)

    def test_append_file(self):
        ''' Make sure append_file() works '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        client.append_file(stream, '1234')  # Whathever works
        self.assertEqual(context.outfp, '1234')

class SendMessage(unittest.TestCase):
    ''' Regression test for code that sends a message '''

    send_complete_cnt = 0

    def handle_send_complete(self, stream):
        ''' Emulates handle_send_complete() '''
        self.send_complete_cnt += 1

    def test_no_body(self):
        ''' Make sure send_message() works without body '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        client.append_request(stream, 'GET', '/', 'HTTP/1.0')
        client.append_header(stream, 'Accept', 'text/plain')
        client.append_header(stream, 'User-Agent', 'Neubot/0.0.1.0')
        client.append_end_of_headers(stream)
        client.send_message(stream)
        self.assertEqual(stream.outs, six.b(''.join([
          'GET / HTTP/1.0\r\n',
          'Accept: text/plain\r\n',
          'User-Agent: Neubot/0.0.1.0\r\n',
          '\r\n'])))

    def test_bytes_body(self):
        ''' Make sure send_message() works with bytes-only body '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        client.append_request(stream, 'GET', '/', 'HTTP/1.0')
        client.append_header(stream, 'Accept', 'text/plain')
        client.append_header(stream, 'User-Agent', 'Neubot/0.0.1.0')
        client.append_header(stream, 'Content-Length', '16')
        client.append_header(stream, 'Content-Type', 'text/plain')
        client.append_end_of_headers(stream)
        client.append_bytes(stream, six.b('A') * 16)
        client.send_message(stream)
        self.assertEqual(stream.outs, six.b(''.join([
          'GET / HTTP/1.0\r\n',
          'Accept: text/plain\r\n',
          'User-Agent: Neubot/0.0.1.0\r\n',
          'Content-Length: 16\r\n',
          'Content-Type: text/plain\r\n',
          '\r\n',
          'A' * 16])))

    def test_fp_body(self):
        ''' Make sure send_message() works with filep body '''

        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        client.append_request(stream, 'GET', '/', 'HTTP/1.0')
        client.append_header(stream, 'Accept', 'text/plain')
        client.append_header(stream, 'User-Agent', 'Neubot/0.0.1.0')
        client.append_header(stream, 'Content-Length',
                             str(3 * http_clnt.MAXREAD - 4))
        client.append_header(stream, 'Content-Type', 'text/plain')
        client.append_end_of_headers(stream)
        stringio = six.BytesIO(six.b('A') * (3 * http_clnt.MAXREAD - 4))
        client.append_file(stream, stringio)

        # Make sure send_complete is called just once and at the end
        self.send_complete_cnt = 0
        client.handle_send_complete = self.handle_send_complete

        # First send() sends just the request headers and should not
        # invoke the send_complete() hook
        client.send_message(stream)
        self.assertEqual(stream.outs, six.b(''.join([
          'GET / HTTP/1.0\r\n',
          'Accept: text/plain\r\n',
          'User-Agent: Neubot/0.0.1.0\r\n',
          'Content-Length: %d\r\n' % (3 * http_clnt.MAXREAD - 4),
          'Content-Type: text/plain\r\n',
          '\r\n'])))
        self.assertEqual(self.send_complete_cnt, 0)

        # Second send() sends the first MAXREAD bytes and should not
        # invoke the send_complete() hook
        client._handle_send_complete(stream)
        self.assertEqual(stream.outs, six.b('A') * http_clnt.MAXREAD)
        self.assertEqual(self.send_complete_cnt, 0)

        # Third send() sends the second MAXREAD bytes and should not
        # invoke the send_complete() hook
        client._handle_send_complete(stream)
        self.assertEqual(stream.outs, six.b('A') * http_clnt.MAXREAD)
        self.assertEqual(self.send_complete_cnt, 0)

        # Fourth send() sends the third MAXREAD bytes and should not
        # invoke the send_complete() hook
        client._handle_send_complete(stream)
        self.assertEqual(stream.outs, six.b('A') * (http_clnt.MAXREAD - 4))
        self.assertEqual(self.send_complete_cnt, 0)

        # Fifth send() should cleanup things, should invoke the
        # send_complete() hook, and clear the output file
        client._handle_send_complete(stream)
        self.assertEqual(context.outfp, None)
        self.assertEqual(self.send_complete_cnt, 1)

    #
    # TODO add test for sending chunked bodies when the code is merged
    # into the master branch.
    #

class HandleData(unittest.TestCase):
    ''' Regression test for HttpClient _handle_data() '''

    lines = []
    pieces = []

    def handle_line(self, stream, line):
        ''' Very simple handle_line() method '''
        self.lines.append(line)

    def handle_piece(self, stream, piece):
        ''' Very simple handle_piece() method '''
        self.pieces.append(piece)

    def test_no_data_open(self):
        ''' Make sure _handle_data() works for no data and open stream '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        client._handle_data(stream, six.b(''))
        # Make sure the code schedules the next recv
        self.assertEqual(stream.count, http_clnt.MAXRECEIVE)
        self.assertEqual(stream.func, client._handle_data)

    def test_no_data_closed(self):
        ''' Make sure _handle_data() works for no data and closed stream '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        stream.isclosed = 1  # Pretend the stream is closed
        client._handle_data(stream, six.b(''))
        # Make sure we don't schedule the next recv
        self.assertEqual(stream.count, 0)
        self.assertEqual(stream.func, None)

    def test_readline_smpl(self):
        ''' Make sure _handle_data() works for reading simple lines '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        bytez = six.b('GET / HTTP/1.0\r\nAccept: */*\r\n\r\n')
        self.lines = []  # Start over
        context.handle_line = self.handle_line
        client._handle_data(stream, bytez)
        # Make sure we have read the three lines
        self.assertEqual(len(self.lines), 3)
        self.assertEqual(self.lines[0], six.b('GET / HTTP/1.0\r\n'))
        self.assertEqual(self.lines[1], six.b('Accept: */*\r\n'))
        self.assertEqual(self.lines[2], six.b('\r\n'))

    def test_readline_partial(self):
        ''' Make sure _handle_data() works for reading partial lines '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.lines = []  # Start over
        context.handle_line = self.handle_line

        # Here we have a partial line so nothing will happen
        bytez = six.b('GET / HTTP/1')
        client._handle_data(stream, bytez)
        self.assertEqual(len(self.lines), 0)

        # Here we resume and split the three input lines
        bytez = six.b('.0\r\nAccept: */*\r\n\r\n')
        client._handle_data(stream, bytez)
        self.assertEqual(len(self.lines), 3)
        self.assertEqual(self.lines[0], six.b('GET / HTTP/1.0\r\n'))
        self.assertEqual(self.lines[1], six.b('Accept: */*\r\n'))
        self.assertEqual(self.lines[2], six.b('\r\n'))

    def test_readline_too_long(self):
        ''' Make sure _handle_data() fails when reading too-long lines '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        bytez = six.b('A') * http_clnt.MAXLINE
        # Note: failure because no LF at line[MAXLINE -1]
        self.assertRaises(RuntimeError, client._handle_data, stream, bytez)

    def test_readpiece_small(self):
        ''' Make sure _handle_data() works for reading small pieces '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        bytez = six.b('A') * 7
        context.left = 7
        self.pieces = []  # Start over
        context.handle_piece = self.handle_piece
        client._handle_data(stream, bytez)
        self.assertEqual(context.left, 0)
        self.assertEqual(len(self.pieces), 1)
        self.assertEqual(self.pieces[0], six.b('A') * 7)

    def test_readpiece_partial(self):
        ''' Make sure _handle_data() works for reading partial pieces '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.pieces = []  # Start over
        context.left = 7
        context.handle_piece = self.handle_piece

        bytez = six.b('A') * 6
        client._handle_data(stream, bytez)
        self.assertEqual(context.left, 7)
        self.assertEqual(len(self.pieces), 0)

        bytez = six.b('A') * 1
        client._handle_data(stream, bytez)
        self.assertEqual(context.left, 0)
        self.assertEqual(len(self.pieces), 1)
        self.assertEqual(self.pieces[0], six.b('A') * 7)

    def test_readpiece_large(self):
        ''' Make sure _handle_data() works for reading large pieces '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.pieces = []  # Start over
        context.left = http_clnt.MAXRECEIVE + 8
        context.handle_piece = self.handle_piece

        bytez = six.b('A') * (http_clnt.MAXRECEIVE + 4)
        client._handle_data(stream, bytez)
        self.assertEqual(context.left, 8)
        self.assertEqual(len(self.pieces), 1)
        self.assertEqual(self.pieces[0], six.b('A') * http_clnt.MAXRECEIVE)

        bytez = six.b('A') * 4
        client._handle_data(stream, bytez)
        self.assertEqual(context.left, 0)
        self.assertEqual(len(self.pieces), 2)
        self.assertEqual(self.pieces[0], six.b('A') * http_clnt.MAXRECEIVE)
        self.assertEqual(self.pieces[1], six.b('A') * 8)

    def test_read_piece_to_line(self):
        ''' Make sure _handle_data() reads lines when done with pieces '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.pieces = []  # Start over
        self.lines = []  # Start over
        context.left = 64
        context.handle_piece = self.handle_piece
        context.handle_line = self.handle_line

        bytez = six.b('').join([six.b('A') * 64,
                                six.b('HTTP/1.1 200 Ok\r\n'),
                                six.b('Content-Type: text/plain\r\n'),
                                six.b('Server: Neubot/0.0.1.0\r\n'),
                                six.b('\r\n')])
        client._handle_data(stream, bytez)

        self.assertEqual(context.left, 0)
        self.assertEqual(len(self.pieces), 1)
        self.assertEqual(self.pieces[0], six.b('A') * 64)

        self.assertEqual(len(self.lines), 4)
        self.assertEqual(self.lines[0], six.b('HTTP/1.1 200 Ok\r\n'))
        self.assertEqual(self.lines[1], six.b('Content-Type: text/plain\r\n'))
        self.assertEqual(self.lines[2], six.b('Server: Neubot/0.0.1.0\r\n'))
        self.assertEqual(self.lines[3], six.b('\r\n'))

    def test_read_line_to_piece(self):
        ''' Make sure _handle_data() reads pieces after lines '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.pieces = []  # Start over
        self.lines = []  # Start over
        context.handle_piece = self.handle_piece
        context.handle_line = self.handle_line

        bytez = six.b('').join([six.b('HTTP/1.1 200 Ok\r\n'),
                                six.b('Content-Type: text/plain\r\n'),
                                six.b('Server: Neubot/0.0.1.0\r\n'),
                                six.b('\r\n'),
                                six.b('A') * 64])
        client._handle_data(stream, bytez)
        self.assertEqual(len(self.lines), 4)
        self.assertEqual(self.lines[0], six.b('HTTP/1.1 200 Ok\r\n'))
        self.assertEqual(self.lines[1], six.b('Content-Type: text/plain\r\n'))
        self.assertEqual(self.lines[2], six.b('Server: Neubot/0.0.1.0\r\n'))
        self.assertEqual(self.lines[3], six.b('\r\n'))

        context.left = 64
        client._handle_data(stream, bytez)
        self.assertEqual(context.left, 0)
        self.assertEqual(len(self.pieces), 1)
        self.assertEqual(self.pieces[0], six.b('A') * 64)

class HandleFirstline(unittest.TestCase):
    ''' Regression test for HttpClient _handle_firstline() '''

    def test_numtokens(self):
        ''' Make sure _handle_firstline() requires 3+ tokens '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.assertRaises(RuntimeError, client._handle_firstline,
                          stream, six.b(''))
        self.assertRaises(RuntimeError, client._handle_firstline,
                          stream, six.b('\r\n'))
        self.assertRaises(RuntimeError, client._handle_firstline,
                          stream, six.b('HTTP/1.0\r\n'))
        self.assertRaises(RuntimeError, client._handle_firstline,
                          stream, six.b('HTTP/1.0 200\r\n'))

    def test_protocol_name(self):
        ''' Make sure _handle_firstline() requires HTTP protocol '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.assertRaises(RuntimeError, client._handle_firstline,
                          stream, six.b('SMTP/1.0 200 Ok\r\n'))

    def test_protocol_version(self):
        ''' Make sure _handle_firstline() requires HTTP/1.{0,1} protocol '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.assertRaises(RuntimeError, client._handle_firstline,
                          stream, six.b('HTTP/1.2 200 Ok\r\n'))

    def test_success(self):
        ''' Make sure _handle_firstline() works as expected '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        client._handle_firstline(stream, six.b('HTTP/1.1 404 Not Found\r\n'))
        self.assertEqual(context.protocol, six.b('HTTP/1.1'))
        self.assertEqual(context.code, six.b('404'))
        self.assertEqual(context.reason, six.b('Not Found'))
        # Make sure state is OK
        self.assertEqual(context.last_hdr, six.b(''))
        self.assertEqual(context.headers, {})
        self.assertEqual(context.handle_line, client._handle_header)

    def test_blanks(self):
        ''' Make sure _handle_firstline() works as expected w/ extra blanks '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)

        client._handle_firstline(stream,
          six.b(' HTTP/1.1   404   Not Found  \r\n'))
        self.assertEqual(context.protocol, six.b('HTTP/1.1'))
        self.assertEqual(context.code, six.b('404'))
        self.assertEqual(context.reason, six.b('Not Found'))

        client._handle_firstline(stream,
          six.b('\tHTTP/1.1\t404\tNot Found\t\r\n'))
        self.assertEqual(context.protocol, six.b('HTTP/1.1'))
        self.assertEqual(context.code, six.b('404'))
        self.assertEqual(context.reason, six.b('Not Found'))

class HandleHeaderEx(unittest.TestCase):
    ''' Regression test for HttpClient _handle_header_ex() '''

    #
    # Start with checking that we recognize the end of headers.  Make
    # sure that we are liberal in what we accept.  E.g., ensure that LF
    # alone is enough to trigger the end-of-headers event.
    #

    handle_done_cnt = 0

    def handle_done(self, stream):
        ''' Trap invocation of handle_done '''
        self.handle_done_cnt += 1

    def test_eoh(self):
        ''' Make sure _handle_header_ex() recognizes EOH '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream, six.b('\r\n'), self.handle_done)
        self.assertEqual(self.handle_done_cnt, 1)

    def test_eoh_lf_only(self):
        ''' Make sure _handle_header_ex() recognizes EOH w/ LF only '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream, six.b('\n'), self.handle_done)
        self.assertEqual(self.handle_done_cnt, 1)

    def test_eoh_space(self):
        ''' Make sure _handle_header_ex() recognizes EOH w/ spaces '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream, six.b(' \r\n'), self.handle_done)
        self.assertEqual(self.handle_done_cnt, 1)

    def test_eoh_tab(self):
        ''' Make sure _handle_header_ex() recognizes EOH w/ tab '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream, six.b('\t\r\n'), self.handle_done)
        self.assertEqual(self.handle_done_cnt, 1)

    def test_eoh_empty(self):
        ''' Make sure _handle_header_ex() recognizes EOH w/ empty string '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream, six.b(''), self.handle_done)
        self.assertEqual(self.handle_done_cnt, 1)

    #
    # Make sure that single-line headers are correctly parsed.  Take into
    # account special cases like multiple headers.  Ensure that the code
    # raises RuntimeError if the line does not contain the ':' separator.
    #

    def test_header_smpl(self):
        ''' Make sure _handle_header_ex() correctly parses simple headers '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream, six.b('Content-Type: text/plain\r\n'),
                                 self.handle_done)
        self.assertEqual(self.handle_done_cnt, 0)
        self.assertTrue(six.b('content-type') in context.headers)
        self.assertFalse(six.b('Content-Type') in context.headers)
        self.assertEqual(context.headers[six.b('content-type')],
                         six.b('text/plain'))

    def test_header_spaces(self):
        ''' Make sure _handle_header_ex() correctly parses headers
            with extra spaces '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream,
          six.b('Content-Type \t: \ttext/plain\t \r\n'),
          self.handle_done)
        self.assertEqual(self.handle_done_cnt, 0)
        self.assertTrue(six.b('content-type') in context.headers)
        self.assertFalse(six.b('Content-Type') in context.headers)
        self.assertEqual(context.headers[six.b('content-type')],
                         six.b('text/plain'))

    def test_header_badfmt(self):
        ''' Make sure _handle_header_ex() errs out on bad header format '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.assertRaises(RuntimeError, client._handle_header_ex, stream,
          six.b('Content-Type text/plain\r\n'), self.handle_done)

    def test_header_multiple(self):
        ''' Make sure _handle_header_ex() correctly parses multiple headers
            with headrs with equal name '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream,
          six.b('Content-Type: text/plain\r\n'),
          self.handle_done)
        client._handle_header_ex(stream,
          six.b('Content-Type: text/plain\r\n'),
          self.handle_done)
        self.assertEqual(self.handle_done_cnt, 0)
        self.assertTrue(six.b('content-type') in context.headers)
        self.assertFalse(six.b('Content-Type') in context.headers)
        self.assertEqual(context.headers[six.b('content-type')],
                         six.b('text/plain, text/plain'))

    def test_header_multiple_spaces(self):
        ''' Make sure _handle_header_ex() correctly parses multiple headers
            with headrs with equal name and spaces '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream,
          six.b('Content-Type :     text/plain    \r\n'),
          self.handle_done)
        client._handle_header_ex(stream,
          six.b('Content-Type\t\t: \ttext/plain\t\r\n'),
          self.handle_done)
        self.assertEqual(self.handle_done_cnt, 0)
        self.assertTrue(six.b('content-type') in context.headers)
        self.assertFalse(six.b('Content-Type') in context.headers)
        self.assertEqual(context.headers[six.b('content-type')],
                         six.b('text/plain, text/plain'))

    #
    # Check whether RFC822 line folding works.  I.e., whether it is possible
    # to continue the value of a header into the next line by putting space
    # at the beginning of it.  Not paramount for Neubot but required since we
    # need to talk with non-Neubot servers too, e.g., Apache.
    #

    def test_nofolding_first_hdr(self):
        ''' Make sure _handle_header_ex() allows first header to start
            with a space or tab '''
        # This is a "feature" of Neubot's HTTP
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream, six.b(' Content-Type: text/plain\r\n'),
                                 self.handle_done)
        self.assertEqual(self.handle_done_cnt, 0)
        self.assertTrue(six.b('content-type') in context.headers)
        self.assertFalse(six.b('Content-Type') in context.headers)
        self.assertEqual(context.headers[six.b('content-type')],
                         six.b('text/plain'))

    def test_folding_space(self):
        ''' Make sure _handle_header_ex() folds line starting with space '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream, six.b('Content-Type: \r\n'),
                                 self.handle_done)
        client._handle_header_ex(stream, six.b(' text/plain\r\n'),
                                 self.handle_done)
        self.assertEqual(self.handle_done_cnt, 0)
        self.assertTrue(six.b('content-type') in context.headers)
        self.assertFalse(six.b('Content-Type') in context.headers)
        self.assertEqual(context.headers[six.b('content-type')],
                         six.b('text/plain'))

    def test_folding_tab(self):
        ''' Make sure _handle_header_ex() folds line starting with tab '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream, six.b('Content-Type: \r\n'),
                                 self.handle_done)
        client._handle_header_ex(stream, six.b('\ttext/plain\r\n'),
                                 self.handle_done)
        self.assertEqual(self.handle_done_cnt, 0)
        self.assertTrue(six.b('content-type') in context.headers)
        self.assertFalse(six.b('Content-Type') in context.headers)
        self.assertEqual(context.headers[six.b('content-type')],
                         six.b('text/plain'))

    def test_folding_multi(self):
        ''' Make sure _handle_header_ex() folds multiple lines '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream, six.b('Accept: \r\n'),
                                 self.handle_done)
        client._handle_header_ex(stream, six.b(' application/json,\r\n'),
                                 self.handle_done)
        client._handle_header_ex(stream, six.b(' text/plain\r\n'),
                                 self.handle_done)
        self.assertEqual(self.handle_done_cnt, 0)
        self.assertTrue(six.b('accept') in context.headers)
        self.assertFalse(six.b('Accept') in context.headers)
        self.assertEqual(context.headers[six.b('accept')],
                         six.b('application/json, text/plain'))

    def test_colon_in_folded_line(self):
        ''' Make sure _handle_header_ex() correctly handles colon
            in folded line '''
        client = http_clnt.HttpClient()
        context = http_clnt.ClientContext({}, None, None)
        stream = FakeStream(context)
        self.handle_done_cnt = 0  # Start over
        client._handle_header_ex(stream, six.b('Accept: \r\n'),
                                 self.handle_done)
        client._handle_header_ex(stream, six.b(' application:json,\r\n'),
                                 self.handle_done)
        client._handle_header_ex(stream, six.b(' text:plain\r\n'),
                                 self.handle_done)
        self.assertEqual(self.handle_done_cnt, 0)
        self.assertTrue(six.b('accept') in context.headers)
        self.assertFalse(six.b('Accept') in context.headers)
        self.assertEqual(context.headers[six.b('accept')],
                         six.b('application:json, text:plain'))

#
# TODO Tests for other methods need to wait 0.4.16.x where the code will
# be more rational and simpler to test.  There is no point in writing them
# now and then have to rework them significantly.  I will instead write
# them directly in the proper branch.
#

if __name__ == '__main__':
    unittest.main()
