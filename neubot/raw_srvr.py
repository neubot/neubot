# neubot/raw_srvr.py

#
# Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>,
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

'''
 Server-side `test` phase of the raw test, minus access control, which is
 implemented in raw_srvr_glue.py.
'''

# Python3-ready: yes

import getopt
import logging
import os
import struct
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.brigade import Brigade
from neubot.defer import Deferred
from neubot.handler import Handler
from neubot.poller import POLLER
from neubot.raw_defs import AUTH_LEN
from neubot.raw_defs import EMPTY_MESSAGE
from neubot.raw_defs import FAKEAUTH
from neubot.raw_defs import RAWTEST
from neubot.raw_defs import RAWTEST_CODE
from neubot.raw_defs import PIECE_CODE
from neubot.raw_defs import PING_CODE
from neubot.raw_defs import PINGBACK
from neubot.stream import Stream

from neubot import six
from neubot import utils
from neubot import utils_net
from neubot import utils_version
from neubot import web100

LEN_MESSAGE = 32768
MAXRECV = 262144

class ServerContext(Brigade):

    ''' Server context '''

    def __init__(self):
        Brigade.__init__(self)
        self.ticks = 0.0
        self.count = 0
        self.message = six.b('')
        self.auth = six.b('')
        self.state = {}
        self.snap_ticks = 0.0
        self.snap_count = 0
        self.snap_utime = 0.0
        self.snap_stime = 0.0
        self.web100_dirname = six.u('')

class RawServer(Handler):

    ''' Raw test server '''

    def handle_accept(self, listener, sock, sslconfig, sslcert):
        logging.info('raw_srvr: new connection at %s', listener)
        Stream(sock, self._connection_ready, self._connection_lost,
          sslconfig, sslcert, ServerContext())

    def handle_accept_error(self, listener):
        logging.warning('raw_srvr: accept failed')

    def _connection_ready(self, stream):
        ''' Invoked when the connection is ready '''
        logging.info('raw_srvr: sending auth to client... in progress')
        context = stream.opaque
        spec = '%s %s' % (utils_net.format_epnt_web100(stream.myname),
                          utils_net.format_epnt_web100(stream.peername))
        context.web100_dirname = web100.web100_find_dirname(
          web100.WEB100_HEADER, spec)
        logging.debug('> FAKEAUTH')
        stream.send(FAKEAUTH, self._fakeauth_sent)

    def _fakeauth_sent(self, stream):
        ''' The FAKEAUTH was sent to client '''
        logging.info('raw_srvr: sending auth to client... complete')
        logging.info('raw_srvr: receiving auth from client... in progress')
        stream.recv(AUTH_LEN, self._waiting_auth)

    def _waiting_auth(self, stream, data):
        ''' Invoked when we're waiting for client auth '''
        context = stream.opaque
        context.bufferise(data)
        tmp = context.pullup(AUTH_LEN)
        if not tmp:
            stream.recv(AUTH_LEN, self._waiting_auth)
            return
        logging.debug('< AUTH')
        self.filter_auth(stream, tmp)
        context.auth = tmp
        context.state['myname'] = stream.myname[0]
        context.state['peername'] = stream.peername[0]
        context.state['platform'] = sys.platform
        context.state['version'] = utils_version.NUMERIC_VERSION
        logging.info('raw_srvr: receiving auth from client... complete')
        logging.info('raw_srvr: waiting for RAWTEST message... in progress')
        stream.recv(len(RAWTEST), self._waiting_rawtest)

    def filter_auth(self, stream, tmp):
        ''' Filter client auth '''

    def _waiting_rawtest(self, stream, data):
        ''' Waiting for RAWTEST message from client '''
        context = stream.opaque
        context.bufferise(data)
        tmp = context.pullup(len(RAWTEST))
        if not tmp:
            stream.recv(len(RAWTEST), self._waiting_rawtest)
            return
        if tmp[4:5] == PING_CODE:
            logging.debug('< PING')
            stream.send(PINGBACK, self._sent_pingback)
            logging.debug('> PINGBACK')
            return
        if tmp[4:5] != RAWTEST_CODE:
            raise RuntimeError('raw_srvr: received invalid message')
        logging.debug('< RAWTEST')
        logging.info('raw_srvr: waiting for RAWTEST message... complete')
        logging.info('raw_srvr: raw test... in progress')
        context.count = context.snap_count = stream.bytes_out
        context.ticks = context.snap_ticks = utils.ticks()
        context.snap_utime, context.snap_stime = os.times()[:2]
        message = PIECE_CODE + context.auth * int(LEN_MESSAGE / AUTH_LEN)
        context.message = struct.pack('!I', len(message)) + message
        stream.send(context.message, self._piece_sent)
        #logging.debug('> PIECE')
        POLLER.sched(1, self._periodic, stream)
        stream.recv(1, self._waiting_eof)

    @staticmethod
    def _waiting_eof(stream, data):
        ''' If this is invoked the protocol was violated '''
        raise RuntimeError('raw_srvr: protocol violation')

    def _sent_pingback(self, stream):
        ''' Sent the PINGBACK message '''
        stream.recv(len(RAWTEST), self._waiting_rawtest)

    def _piece_sent(self, stream):
        ''' Invoked when a message has been sent '''
        context = stream.opaque
        ticks = utils.ticks()
        if ticks - context.ticks < 10:
            stream.send(context.message, self._piece_sent)
            #logging.debug('> PIECE')
            return
        logging.info('raw_srvr: raw test... complete')
        ticks = utils.ticks()
        timediff = ticks - context.ticks
        bytesdiff = stream.bytes_out - context.count
        context.state['timestamp'] = utils.timestamp()
        context.state['goodput'] = {
                                    'ticks': ticks,
                                    'bytesdiff': bytesdiff,
                                    'timediff': timediff,
                                   }
        if timediff > 1e-06:
            speed = utils.speed_formatter(bytesdiff / timediff)
            logging.info('raw_srvr: goodput: %s', speed)
        self._periodic_internal(stream)
        stream.send(EMPTY_MESSAGE, self._empty_message_sent)
        logging.debug('> {empty-message}')

    def _periodic(self, args):
        ''' Periodically snap goodput '''
        stream = args[0]
        if stream.opaque:
            deferred = Deferred()
            deferred.add_callback(self._periodic_internal)
            deferred.add_errback(lambda err: self._periodic_error(stream, err))
            deferred.callback(stream)
            POLLER.sched(1, self._periodic, stream)

    @staticmethod
    def _periodic_error(stream, err):
        ''' Invoked when _periodic_internal() fails '''
        logging.warning('raw_clnt: _periodic_internal() failed: %s', err)
        stream.close()

    @staticmethod
    def _periodic_internal(stream):
        ''' Periodically snap goodput (internal function) '''
        context = stream.opaque
        utime, stime = os.times()[:2]
        utimediff = utime - context.snap_utime
        stimediff = stime - context.snap_stime
        ticks = utils.ticks()
        timediff = ticks - context.snap_ticks
        bytesdiff = stream.bytes_out - context.snap_count
        context.state.setdefault('goodput_snap', []).append({
          'ticks': ticks, 'bytesdiff': bytesdiff, 'timediff': timediff,
          'utimediff': utimediff, 'stimediff': stimediff})
        logging.debug('raw_srvr: utime, stime = %f, %f', utime, stime)
        if timediff > 1e-06:
            speed = utils.speed_formatter(bytesdiff / timediff)
            logging.debug('raw_srvr: goodput_snap: %s', speed)
        web100_snap = web100.web100_snap(web100.WEB100_HEADER,
          context.web100_dirname)
        web100_snap['ticks'] = ticks
        context.state.setdefault('web100_snap', []).append(web100_snap)
        context.snap_count = stream.bytes_out
        context.snap_ticks = ticks
        context.snap_utime = utime
        context.snap_stime = stime

    @staticmethod
    def _empty_message_sent(stream):
        ''' Sent the empty message to signal end of test '''
        # Tell the poller to reclaim this stream in some seconds
        stream.created = utils.ticks()
        stream.watchdog = 5

    def _connection_lost(self, stream):
        ''' Invoked when the connection is lost '''

def main(args):
    ''' Main function '''

    try:
        options, arguments = getopt.getopt(args[1:], '6A:p:Sv')
    except getopt.error:
        sys.exit('usage: neubot mod_raw [-6Sv] [-A address] [-p port]')
    if arguments:
        sys.exit('usage: neubot mod_raw [-6Sv] [-A address] [-p port]')

    prefer_ipv6 = 0
    address = '127.0.0.1'
    port = 12345
    sslconfig = False
    sslcert = ''
    verbose = 0
    for name, value in options:
        if name == '-6':
            prefer_ipv6 = 1
        elif name == '-A':
            address = value
        elif name == '-p':
            port = int(value)
        elif name == '-S':
            sslconfig = True
            sslcert = 'cert.pem'
        elif name == '-v':
            verbose += 1

    level = logging.INFO
    if verbose > 0:
        level = logging.DEBUG
    logging.getLogger().setLevel(level)

    handler = RawServer()
    handler.listen((address, port), prefer_ipv6, sslconfig, sslcert)
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
