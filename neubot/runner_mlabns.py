# neubot/runner_mlabns.py

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

'''
  Runner for mlab-ns service (which allows to discover the closest M-Lab
  node, or a random node).
'''

# Python3-ready: yes

import getopt
import logging
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.compat import json
from neubot.http_clnt import HttpClient
from neubot.notify import NOTIFIER
from neubot.poller import POLLER
from neubot.runner_hosts import RUNNER_HOSTS

from neubot import http_utils
from neubot import six
from neubot import utils_net
from neubot import utils_version

APPLICATION_JSON = six.b('application/json')
CODE200 = six.b('200')
CONTENT_TYPE = six.b('content-type')

class RunnerMlabns(HttpClient):
    ''' Runner client for mlab-ns '''

    def connect(self, endpoint, prefer_ipv6, sslconfig, extra):
        logging.info('runner_mlabns: server discovery... in progress')
        extra['address'] = endpoint[0]
        extra['port'] = endpoint[1]
        extra['requests'] = 0
        if extra['policy'] not in ('random', ''):
            raise RuntimeError('runner_mlabns: unknown policy')
        return HttpClient.connect(self, endpoint, prefer_ipv6, sslconfig, extra)

    def handle_connect_error(self, connector):
        logging.info('runner_mlabns: server discovery... connect() failed')
        NOTIFIER.publish('testdone')  # Tell the runner we're done

    def handle_connect(self, connector, sock, rtt, sslconfig, extra):
        self.create_stream(sock, self.handle_connection_made,
          self.handle_connection_lost, sslconfig, None, extra)

    @staticmethod
    def handle_connection_lost(stream):
        ''' Invoked when the connection is lost '''
        logging.info('runner_mlabns: server discovery... complete')
        NOTIFIER.publish('testdone')  # Tell the runner we're done

    def handle_connection_made(self, stream):
        ''' Invoked when the connection is established '''
        logging.debug('runner_mlabns: query... in progress')
        context = stream.opaque
        extra = context.extra
        uri = '/neubot'
        if extra['policy'] == 'random':
            uri = '/neubot?policy=random'
        host_header = utils_net.format_epnt((extra['address'], extra['port']))
        self.append_request(stream, 'GET', uri, 'HTTP/1.1')
        self.append_header(stream, 'Host', host_header)
        self.append_header(stream, 'User-Agent', utils_version.HTTP_HEADER)
        self.append_header(stream, 'Cache-Control', 'no-cache')
        self.append_header(stream, 'Pragma', 'no-cache')
        #self.append_header(stream, 'Connection', 'close')
        self.append_end_of_headers(stream)
        self.send_message(stream)
        context.body = http_utils.Body()  # Want to save body
        extra['requests'] += 1

    def handle_end_of_body(self, stream):
        HttpClient.handle_end_of_body(self, stream)
        context = stream.opaque
        extra = context.extra
        if extra['requests'] <= 0:
            raise RuntimeError('runner_mlabns: unexpected response')
        extra['requests'] -= 1
        tmp = context.headers.get(CONTENT_TYPE)
        if context.code != CODE200 or tmp != APPLICATION_JSON:
            logging.error('runner_mlabns: bad response')
            stream.close()
            return
        content = six.bytes_to_string(context.body.getvalue(), 'utf-8')
        response = json.loads(content)
        http_utils.prettyprint_json(response, '<')
        if extra['policy'] == 'random':
            RUNNER_HOSTS.set_random_host(response)
        else:
            RUNNER_HOSTS.set_closest_host(response)
        stream.close()

USAGE = 'usage: neubot runner_mlabns [-6Sv] [-A address] [-P policy] [-p port]'

def main(args):
    ''' Main function '''
    try:
        options, arguments = getopt.getopt(args[1:], '6A:P:p:Sv')
    except getopt.error:
        sys.exit(USAGE)
    if arguments:
        sys.exit(USAGE)

    prefer_ipv6 = 0
    address = 'mlab-ns.appspot.com'
    policy = ''
    port = 80
    sslconfig = 0
    level = logging.INFO
    for name, value in options:
        if name == '-6':
            prefer_ipv6 = 1
        elif name == '-A':
            address = value
        elif name == '-P':
            policy = value
        elif name == '-p':
            port = int(value)
        elif name == '-S':
            sslconfig = 1
        elif name == '-v':
            level = logging.DEBUG

    logging.getLogger().setLevel(level)

    handler = RunnerMlabns()
    extra = {'policy': policy}
    handler.connect((address, port), prefer_ipv6, sslconfig, extra)
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
