# neubot/raw_negotiate.py

#
# Copyright (c) 2010-2012
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

'''
 Client-side `negotiate` and `collect` phases of the raw test.  Invokes code in
 raw_clnt.py for the `test` phase.
'''

# Adapted from neubot/bittorrent/client.py

#
# This file contains the negotiator client of the RAW test, i.e. the code that
# negotiates with the test server and collects the results.
#

import getopt
import logging
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.backend import BACKEND
from neubot.config import CONFIG
from neubot.compat import json
from neubot.defer import Deferred
from neubot.http_clnt import HttpClient
from neubot.notify import NOTIFIER
from neubot.poller import POLLER
from neubot.raw_clnt import RawClient
from neubot.state import STATE

from neubot import http_utils
from neubot import raw_analyze
from neubot import six
from neubot import utils_net
from neubot import utils_version

APPLICATION_JSON = six.b('application/json')
CODE200 = six.b('200')
CONTENT_TYPE = six.b('content-type')

class RawNegotiate(HttpClient):

    ''' Raw negotiate client '''

    def connect(self, endpoint, prefer_ipv6, sslconfig, extra):

        # Reset web interface
        STATE.update('test_latency', '---', publish=False)
        STATE.update('test_download', '---', publish=False)
        STATE.update('test_upload', '---', publish=False)
        STATE.update('test_progress', '0%', publish=False)
        STATE.update('test_name', 'raw', publish=False)
        STATE.update('negotiate')

        # Variables
        extra['address'] = endpoint[0]
        extra['authorization'] = ''
        extra['local_result'] = None
        extra['port'] = endpoint[1]
        extra['prefer_ipv6'] = prefer_ipv6
        extra['requests'] = 0
        extra['saved_stream'] = None
        extra['final_state'] = 0

        return HttpClient.connect(self, endpoint, prefer_ipv6, sslconfig, extra)

    def handle_connect_error(self, connector):
        logging.warning('raw_negotiate: connect() failed')
        NOTIFIER.publish('testdone')

    def handle_connect(self, connector, sock, rtt, sslconfig, extra):
        self.create_stream(sock, self.handle_connection_made,
          self.handle_connection_lost, sslconfig, None, extra)

    @staticmethod
    def handle_connection_lost(stream):
        ''' Invoked when the connection is lost '''
        final_state = 0
        context = stream.opaque
        if context:
            extra = context.extra
            if extra:
                final_state = extra['final_state']
        if not final_state:
            logging.warning('raw_negotiate: not reached final state')
        NOTIFIER.publish('testdone')  # Tell the runner we're done

    def handle_connection_made(self, stream):
        ''' Invoked when the connection is established '''
        # Note: this function MUST be callable multiple times
        logging.debug('raw_negotiate: negotiation in progress...')
        context = stream.opaque
        extra = context.extra
        request = {}  # No options for now
        body = six.b(json.dumps(request))
        host_header = utils_net.format_epnt((extra['address'], extra['port']))
        self.append_request(stream, 'POST', '/negotiate/raw', 'HTTP/1.1')
        self.append_header(stream, 'Host', host_header)
        self.append_header(stream, 'User-Agent', utils_version.HTTP_HEADER)
        self.append_header(stream, 'Content-Type', 'application/json')
        self.append_header(stream, 'Content-Length', str(len(body)))
        self.append_header(stream, 'Cache-Control', 'no-cache')
        self.append_header(stream, 'Pragma', 'no-cache')
        if extra['authorization']:
            self.append_header(stream, 'Authorization', extra['authorization'])
        self.append_end_of_headers(stream)
        self.append_bytes(stream, body)
        http_utils.prettyprint_json(request, '>')
        self.send_message(stream)
        context.body = six.StringIO()  # Want to save body
        extra['requests'] += 1

    def handle_end_of_body(self, stream):
        # Note: this function MUST be callable multiple times
        HttpClient.handle_end_of_body(self, stream)
        context = stream.opaque
        extra = context.extra
        if extra['requests'] <= 0:
            raise RuntimeError('raw_negotiate: unexpected response')
        extra['requests'] -= 1
        tmp = context.headers.get(CONTENT_TYPE)
        if context.code != CODE200 or tmp != APPLICATION_JSON:
            logging.error('raw_negotiate: bad response')
            stream.close()
            return
        response = json.loads(six.u(context.body.getvalue()))
        http_utils.prettyprint_json(response, '<')
        if STATE.current == 'negotiate':
            self._process_negotiate_response(stream, response)
        elif STATE.current == 'collect':
            self._process_collect_response(stream, response)
        else:
            raise RuntimeError('raw_negotiate: internal error')

    #
    # The response from the server MUST be a dictionary and MUST contain at
    # least the following fields:
    #
    # authorization: authorization information
    # port: port to connect to
    # queue_pos: current position in queue
    # unchoked: whether the client can run the test now or not
    #

    def _process_negotiate_response(self, stream, response):
        ''' Process response when in negotiate state '''
        # Note: this function MUST be callable multiple times
        extra = stream.opaque.extra
        extra['authorization'] = response['authorization']
        if response['unchoked']:
            logging.debug('raw_negotiate: negotiate complete... unchoked')
            response['address'] = extra['address']  # XXX
            logging.debug('raw_negotiate: test in progress...')
            deferred = Deferred()
            deferred.add_callback(self._start_test)
            errback = lambda error: self._handle_test_failure(stream, error)
            deferred.add_errback(errback)
            successback = lambda state: self._handle_test_success(stream, state)
            deferred.callback((successback, errback, response, extra))
            return
        queue_pos = response['queue_pos']
        logging.debug('raw_negotiate: negotiate complete... in queue (%d)',
          queue_pos)
        STATE.update('negotiate', {'queue_pos': queue_pos})
        self.handle_connection_made(stream)  # Tail call (sort of)

    @staticmethod
    def _start_test(opaque):
        ''' Start RAW test '''
        on_success, on_failure, response, extra = opaque
        state = {
           'authorization': response['authorization'].decode('hex'),
           'on_success': on_success,
           'on_failure': on_failure,
        }
        client = RawClient()
        connector = client.connect((response['address'], response['port']),
                       extra['prefer_ipv6'], 0, state)
        connector.register_errfunc(lambda arg: on_failure('connect failed'))

    def _handle_test_success(self, stream, state):
        ''' Invoked when the test succeeds '''
        logging.debug('raw_negotiate: test complete... success')
        result = {
                  'al_capacity': raw_analyze.compute_bottleneck_capacity(
                     state['rcvr_data'], state['mss']),
                  'al_mss': state['mss'],
                  'al_rexmits': raw_analyze.select_likely_rexmits(
                     state['rcvr_data'], state['connect_time'], state['mss']),
                  'alrtt_list': state['alrtt_list'],
                  'alrtt_avg': state['alrtt_avg'],
                  'connect_time': state['connect_time'],
                  'goodput': state['goodput'],
                  'goodput_snap': state['goodput_snap'],
                  'myname': state['myname'],
                  'peername': state['peername'],
                  'platform': sys.platform,
                  'uuid': CONFIG['uuid'],
                  'version': utils_version.NUMERIC_VERSION,
                 }
        self._start_collect(stream, result)

    @staticmethod
    def _handle_test_failure(stream, error):
        ''' Invoked when the test fails '''
        logging.warning('raw_negotiate: test failed: %s', str(error))
        stream.close()

    def _start_collect(self, stream, result):
        ''' Start the COLLECT phase '''
        STATE.update('collect')
        logging.debug('raw_negotiate: collect in progress...')
        context = stream.opaque
        extra = context.extra
        extra['local_result'] = result
        body = six.b(json.dumps(result))
        host_header = utils_net.format_epnt((extra['address'], extra['port']))
        self.append_request(stream, 'POST', '/collect/raw', 'HTTP/1.1')
        self.append_header(stream, 'Host', host_header)
        self.append_header(stream, 'User-Agent', utils_version.HTTP_HEADER)
        self.append_header(stream, 'Content-Type', 'application/json')
        self.append_header(stream, 'Content-Length', str(len(body)))
        self.append_header(stream, 'Cache-Control', 'no-cache')
        self.append_header(stream, 'Pragma', 'no-cache')
        self.append_header(stream, 'Connection', 'close')
        if extra['authorization']:
            self.append_header(stream, 'Authorization', extra['authorization'])
        self.append_end_of_headers(stream)
        self.append_bytes(stream, body)
        http_utils.prettyprint_json(result, '>')
        self.send_message(stream)
        context.body = six.StringIO()  # Want to save body
        extra['requests'] += 1

    def _process_collect_response(self, stream, remote_result):
        ''' Process response when in collect state '''
        context = stream.opaque
        extra = context.extra
        tmp = context.headers.get(CONTENT_TYPE)
        if context.code != CODE200 or tmp != APPLICATION_JSON:
            logging.warning('raw_negotiate: collect complete... bad response')
            stream.close()
            return
        deferred = Deferred()
        deferred.add_callback(self._save_results)
        deferred.callback((extra['local_result'], remote_result))
        extra['final_state'] = 1
        stream.close()

    @staticmethod
    def _save_results(opaque):
        ''' Save test results '''
        local_result, remote_result = opaque
        remote_result['web100_snap'] = []  # XXX disabled for 0.4.15
        complete_result = {'client': local_result, 'server': remote_result}
        BACKEND.store_raw(complete_result)

def main(args):
    ''' Main function '''
    try:
        options, arguments = getopt.getopt(args[1:], '6A:p:v')
    except getopt.error:
        sys.exit('usage: neubot raw_negotiate [-6v] [-A address] [-p port]')
    if arguments:
        sys.exit('usage: neubot raw_negotiate [-6v] [-A address] [-p port]')

    prefer_ipv6 = 0
    address = '127.0.0.1'
    port = 8080
    level = logging.INFO
    for name, value in options:
        if name == '-6':
            prefer_ipv6 = 1
        elif name == '-A':
            address = value
        elif name == '-p':
            port = int(value)
        elif name == '-v':
            level = logging.DEBUG

    logging.getLogger().setLevel(level)

    handler = RawNegotiate()
    handler.connect((address, port), prefer_ipv6, 0, {})
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
