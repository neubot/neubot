# neubot/raw_clnt.py

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
 Client-side `test` phase of the raw test.  Typically invoked by code that
 lives in raw_negotiate.py.
'''

# Python3-ready: yes

import logging
import getopt
import os
import socket
import struct
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.brigade import Brigade
from neubot.defer import Deferred
from neubot.handler import Handler
from neubot.poller import POLLER
from neubot.raw_defs import FAKEAUTH
from neubot.raw_defs import PING
from neubot.raw_defs import PINGBACK
from neubot.raw_defs import PINGBACK_CODE
from neubot.raw_defs import RAWTEST
from neubot.state import STATE
from neubot.stream import Stream

from neubot import utils

AUTH_LEN = 64
LEN_MESSAGE = 32768
MAXRECV = 262144

class ClientContext(Brigade):

    ''' Client context '''

    def __init__(self, state):
        Brigade.__init__(self)
        self.ticks = 0.0
        self.count = 0
        self.left = 0
        self.snap_ticks = 0.0
        self.snap_count = 0
        self.snap_utime = 0.0
        self.snap_stime = 0.0
        self.state = state
        self.alrtt_ticks = 0.0
        self.alrtt_cnt = 10

class RawClient(Handler):

    ''' Raw test client '''

    def handle_connect(self, connector, sock, rtt, sslconfig, state):
        logging.info('raw_clnt: connection established with %s', connector)
        logging.info('raw_clnt: connect_time: %s', utils.time_formatter(rtt))
        state['connect_time'] = rtt
        Stream(sock, self._connection_ready, self._connection_lost,
          sslconfig, '', ClientContext(state))
        STATE.update('test', 'raw')
        state['mss'] = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG)
        state['rcvr_data'] = []

    def _connection_ready(self, stream):
        ''' Invoked when the connection is ready '''
        logging.info('raw_clnt: sending auth to server... in progress')
        context = stream.opaque
        auth = context.state.get('authorization')
        if not auth:
            logging.warning('raw_clnt: no auth, sending fake auth')
            auth = FAKEAUTH
        logging.debug('> AUTH')
        stream.send(auth, self._auth_sent)

    def _auth_sent(self, stream):
        ''' Invoked when the auth has been sent '''
        logging.info('raw_clnt: sending auth to server... complete')
        logging.info('raw_clnt: receiving auth from server... in progress')
        stream.recv(len(FAKEAUTH), self._waiting_auth)

    def _waiting_auth(self, stream, data):
        ''' Invoked when waiting for AUTH '''
        context = stream.opaque
        context.bufferise(data)
        tmp = context.pullup(len(FAKEAUTH))
        if not tmp:
            stream.recv(len(FAKEAUTH), self._waiting_auth)
            return
        logging.debug('< FAKEAUTH')
        if tmp != FAKEAUTH:
            logging.warning('raw_clnt: nonfake auth from server')
        logging.info('raw_clnt: receiving auth from server... complete')
        logging.info('raw_clnt: estimating ALRTT... in progress')
        self._send_ping(stream)

    def _send_ping(self, stream):
        ''' Sends the PING message '''
        logging.debug('> PING')
        stream.send(PING, self._ping_sent)
        context = stream.opaque
        context.alrtt_ticks = utils.ticks()

    def _ping_sent(self, stream):
        ''' Invoked when the PING message has been sent '''
        stream.recv(len(PINGBACK), self._waiting_pingback)

    def _waiting_pingback(self, stream, data):
        ''' Invoke when waiting for PINGBACK '''
        context = stream.opaque
        context.bufferise(data)
        tmp = context.pullup(len(PINGBACK))
        if not tmp:
            stream.recv(len(PINGBACK), self._waiting_pingback)
            return
        if tmp[4:5] != PINGBACK_CODE:
            raise RuntimeError('raw_clnt: received invalid message')
        timediff = utils.ticks() - context.alrtt_ticks
        context.state.setdefault('alrtt_list', []).append(timediff)
        logging.debug('< PINGBACK')
        logging.debug('raw_clnt: alrtt_sample: %f', timediff)
        context.alrtt_cnt -= 1
        if context.alrtt_cnt > 0:
            self._send_ping(stream)
            return
        alrtt_list = context.state['alrtt_list']
        alrtt_avg = sum(alrtt_list) / len(alrtt_list)
        context.state['alrtt_avg'] = alrtt_avg
        latency = utils.time_formatter(alrtt_avg)
        logging.info('raw_clnt: alrtt_avg: %s', latency)
        STATE.update("test_progress", "50%", publish=False)
        STATE.update('test_latency', latency)
        logging.info('raw_clnt: estimating ALRTT... complete')
        logging.info('raw_clnt: raw goodput test... in progress')
        logging.debug('> RAWTEST')
        stream.send(RAWTEST, self._rawtest_sent)

    def _rawtest_sent(self, stream):
        ''' The RAWTEST message has been sent '''
        stream.recv(MAXRECV, self._waiting_piece)

    def _waiting_piece(self, stream, data):
        ''' Invoked when new data is available '''
        # Note: this loop cannot be adapted to process other messages
        # easily, as pointed out in <raw_defs.py>.
        context = stream.opaque
        context.bufferise(data)
        context.state['rcvr_data'].append((utils.ticks(), len(data)))
        while True:
            if context.left > 0:
                context.left = context.skip(context.left)
                if context.left > 0:
                    break
            elif context.left == 0:
                tmp = context.pullup(4)
                if not tmp:
                    break
                context.left, = struct.unpack('!I', tmp)
                if context.left > MAXRECV:
                    raise RuntimeError('raw_clnt: PIECE too large')
                if not context.ticks:
                    context.ticks = context.snap_ticks = utils.ticks()
                    context.count = context.snap_count = stream.bytes_in
                    context.snap_utime, context.snap_stime = os.times()[:2]
                    POLLER.sched(1, self._periodic, stream)
                if context.left == 0:
                    logging.debug('< {empty-message}')
                    logging.info('raw_clnt: raw goodput test... complete')
                    ticks = utils.ticks()
                    timediff = ticks - context.ticks
                    bytesdiff = stream.bytes_in - context.count
                    context.state['goodput'] = {
                                                'ticks': ticks,
                                                'bytesdiff': bytesdiff,
                                                'timediff': timediff,
                                               }
                    if timediff > 1e-06:
                        speed = utils.speed_formatter(bytesdiff / timediff)
                        logging.info('raw_clnt: goodput: %s', speed)
                        STATE.update("test_progress", "100%", publish=False)
                        STATE.update('test_download', speed, publish=0)
                        STATE.update('test_upload', 'N/A')
                    self._periodic_internal(stream)
                    context.state['complete'] = 1
                    stream.close()
                    return
            else:
                raise RuntimeError('raw_clnt: internal error')
        stream.recv(MAXRECV, self._waiting_piece)

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
        bytesdiff = stream.bytes_in - context.snap_count
        context.state.setdefault('goodput_snap', []).append({
          'ticks': ticks, 'bytesdiff': bytesdiff, 'timediff': timediff,
          'utimediff': utimediff, 'stimediff': stimediff})
        logging.debug('raw_clnt: utime, stime = %f, %f', utime, stime)
        if timediff > 1e-06:
            speed = utils.speed_formatter(bytesdiff / timediff)
            logging.debug('raw_clnt: goodput_snap: %s', speed)
        context.snap_count = stream.bytes_in
        context.snap_ticks = ticks
        context.snap_utime = utime
        context.snap_stime = stime

    def _connection_lost(self, stream):
        ''' Invoked when the connection is lost '''
        deferred = Deferred()
        deferred.add_callback(self._connection_lost_internal)
        deferred.add_errback(lambda error: self._connection_lost_error(stream,
                                                                       error))
        deferred.callback(stream)

    @staticmethod
    def _connection_lost_internal(stream):
        ''' Invoked when the connection is lost (internal func) '''
        if not stream.opaque:
            raise RuntimeError('raw_clnt: no stream opaque')
        context = stream.opaque
        tmp = context.state.get('complete')
        if not tmp:
            raise RuntimeError('raw_clnt: connection unexpectedly closed')
        on_success = context.state.get('on_success')
        if not on_success:
            return
        context.state['myname'] = stream.myname[0]
        context.state['peername'] = stream.peername[0]
        on_success(context.state)

    @staticmethod
    def _connection_lost_error(stream, err):
        ''' Invoked when _connection_lost_internal() fails '''
        logging.warning('raw_clnt: _connection_lost_internal() failed: %s', err)
        context = stream.opaque
        if context:
            on_failure = context.state.get('on_failure')
            if on_failure:
                on_failure('connection unexpectedly closed')

def main(args):
    ''' Main function '''

    try:
        options, arguments = getopt.getopt(args[1:], '6A:p:Sv')
    except getopt.error:
        sys.exit('usage: neubot raw_clnt [-6Sv] [-A address] [-p port]')
    if arguments:
        sys.exit('usage: neubot raw_clnt [-6Sv] [-A address] [-p port]')

    prefer_ipv6 = 0
    address = '127.0.0.1'
    port = 12345
    sslconfig = False
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
        elif name == '-v':
            verbose += 1

    level = logging.INFO
    if verbose > 0:
        level = logging.DEBUG
    logging.getLogger().setLevel(level)

    handler = RawClient()
    handler.connect((address, port), prefer_ipv6, sslconfig, {})
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
