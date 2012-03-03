# neubot/runner_rendezvous.py

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

''' Run rendezvous when the runner needs that '''

# Adapted from neubot/rendezvous/client.py

import getopt
import logging
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.http.client import ClientHTTP
from neubot.http.message import Message

from neubot.compat import json
from neubot.config import CONFIG
from neubot.log import LOG
from neubot.net.poller import POLLER
from neubot.notify import NOTIFIER
from neubot.runner_tests import RUNNER_TESTS
from neubot.runner_updates import RUNNER_UPDATES
from neubot.state import STATE

from neubot import marshal

class RunnerRendezvous(ClientHTTP):
    ''' Rendezvous client '''

    def start_rendezvous(self, uri):
        ''' Starts a rendezvous '''
        logging.info('runner_rendezvous: connecting to %s', uri)
        STATE.update('rendezvous')
        self.connect_uri(uri)

    def connection_failed(self, connector, exception):
        ''' Invoked when the connection fails '''
        STATE.update('rendezvous', {'status': 'failed'})
        NOTIFIER.publish('testdone')
        logging.error('runner_rendezvous: connection failed: %s', exception)

    def connection_lost(self, stream):
        ''' Invoked when the connection is closed or lost '''
        NOTIFIER.publish('testdone')

    def connection_ready(self, stream):
        ''' Invoked when the connection is ready '''

        message = {
                   'accept': ['speedtest', 'bittorrent'],
                   'version': '0.4.9',
                   'privacy_informed': CONFIG['privacy.informed'],
                   'privacy_can_collect': CONFIG['privacy.can_collect'],
                   # Sending on the wire the old name for backward compat
                   'privacy_can_share': CONFIG['privacy.can_publish'],
                  }

        logging.debug('runner_rendezvous: request body %s', message)

        request = Message()
        request.compose(method='GET', pathquery='/rendezvous',
          mimetype='text/xml', keepalive=False, host=self.host_header,
          body=marshal.dict_to_xml('RendezvousRequest', message))

        stream.send_request(request)

    def got_response(self, stream, request, response):
        ''' Invoked when the response is received '''

        if response.code != '200':
            logging.info('runner_rendezvous: bad response')
            stream.close()
            return

        message = json.load(response.body)

        RUNNER_TESTS.update(message['available'])
        RUNNER_UPDATES.update(message['update'])

        logging.info('runner_rendezvous: rendezvous complete')
        stream.close()

def run(uri):
    ''' Rendezvous at URI '''
    client = RunnerRendezvous(POLLER)
    client.configure(CONFIG.copy())
    client.start_rendezvous(uri)

def main(args):
    ''' main() function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'vy')
    except getopt.error:
        sys.exit('usage: neubot runner_rendezvous [-vy] uri')
    if len(arguments) != 1:
        sys.exit('usage: neubot runner_rendezvous [-vy] uri')

    for tpl in options:
        if tpl[0] == '-v':
            LOG.verbose()
        elif tpl[0] == '-y':
            CONFIG.conf.update({
                                'privacy.informed': 1,
                                'privacy.can_collect': 1,
                                'privacy.can_publish': 1
                               })

    run(arguments[0])
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
