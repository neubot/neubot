# neubot/background_api.py

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

def start_api(address=None, port=None):
    ''' Starts API for background module '''

    logging.debug('background_api: starting API server...')

    # Honor /etc/neubot/api
    settings = utils_rc.parse_safe(utils_hier.APIFILEPATH)
    if not address:
        address = settings.get('address', '::1 127.0.0.1')
    if not port:
        port = settings.get('port', '9774')

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
    ''' Main function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'A:p:v')
    except getopt.error:
        sys.exit('usage: neubot background_api [-v] [-A address] [-p port]')
    if arguments:
        sys.exit('usage: neubot background_api [-v] [-A address] [-p port]')

    address = None
    port = None
    for name, value in options:
        if name == '-A':
            address = value
        elif name == '-p':
            port = int(value)
        elif name == '-v':
            CONFIG['verbose'] = 1

    start_api(address, port)
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
