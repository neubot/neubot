# neubot/runner_dload.py

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

''' Nonblocking downloader invoked via runner '''

#
# This is used by Win32 auto-updater only, which runs in the
# same process context of neubot itself and uses the runner
# mechanism: (a) to avoid interfering with tests; (b) to avoid
# blocking the web user interface when downloading an update.
#

import logging
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.http.client import ClientHTTP
from neubot.http.message import Message

from neubot.config import CONFIG
from neubot.poller import POLLER
from neubot.notify import NOTIFIER

from neubot import utils_version

class RunnerDload(ClientHTTP):
    ''' Nonblocking downloader invoked via runner '''

    def __init__(self, ctx):
        ''' Download a file '''
        self.ctx = ctx
        ClientHTTP.__init__(self, POLLER)
        self.configure(CONFIG.copy())
        logging.debug('runner_dload: GET %s', self.ctx['uri'])
        self.connect_uri(self.ctx['uri'])

    def connection_failed(self, connector, exception):
        ''' Invoked when the connection fails '''
        logging.error('runner_dload: connection failed: %s', exception)
        self.ctx['result'] = (-1, None, exception)
        NOTIFIER.publish('testdone')

    def connection_lost(self, stream):
        ''' Invoked when the connection is closed or lost '''
        NOTIFIER.publish('testdone')

    def connection_ready(self, stream):
        ''' Invoked when the connection is ready '''
        request = Message()
        request.compose(method='GET', uri=self.ctx['uri'], keepalive=False)
        request['user-agent'] = utils_version.HTTP_HEADER
        stream.send_request(request)

    def got_response(self, stream, request, response):
        ''' Invoked when the response is received '''

        if response.code != '200':
            logging.error('runner_dload: bad response')
            self.ctx['result'] = (-1, None, 'Bad response')
            stream.close()
            return

        body = response.body.read()
        logging.debug('runner_dload: dload complete and OK')
        self.ctx['result'] = (len(body), body, None)

        stream.close()

def default_callback(ctx):
    ''' Default callback '''
    result = ctx['result']
    if result[0] >= 0:
        sys.stdout.write(result[1])
        sys.stdout.flush()
    else:
        sys.stderr.write('error: %s\n' % str(result[2]))

def main(args):
    ''' main() function '''

    CONFIG['verbose'] = 1

    ctx = {'uri': args[1]}
    RunnerDload(ctx)
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
