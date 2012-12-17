# neubot/background_api.py

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

''' Starts API for background module '''

import getopt
import logging
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.api_server import API_SERVER
from neubot.config import CONFIG
from neubot.http.server import HTTP_SERVER
from neubot.poller import POLLER

from neubot import utils_rc
from neubot import utils_hier

def start(address, port):
    ''' Starts API for background module '''

    logging.debug('background_api: starting API server...')

    # Configure HTTP server
    conf = CONFIG.copy()
    logging.debug('background_api: API server rootdir: %s',
                  utils_hier.WWWDIR)
    conf['http.server.rootdir'] = utils_hier.WWWDIR
    conf['http.server.ssi'] = True
    conf['http.server.bind_or_die'] = True
    HTTP_SERVER.configure(conf)

    # Bind HTTP server to API server
    HTTP_SERVER.register_child(API_SERVER, '/api')

    # Bind HTTP server to address and port
    HTTP_SERVER.listen((address, port))

    logging.debug('background_api: starting API server... done')

def main(args):
    ''' Run the API server '''

    try:
        options, arguments = getopt.getopt(args[1:], 'O:v')
    except getopt.error:
        sys.exit('usage: neubot background_api [-v] [-O setting]')
    if arguments:
        sys.exit('usage: neubot background_api [-v] [-O setting]')

    settings = []
    for name, value in options:
        if name == '-O':
            settings.append(value)
        elif name == '-v':
            CONFIG['verbose'] = 1

    settings = utils_rc.parse_safe(iterable=settings)
    if not 'address' in settings:
        settings['address'] = '127.0.0.1 ::1'
    if not 'port' in settings:
        settings['port'] = '9774'

    start(settings['address'], settings['port'])
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
