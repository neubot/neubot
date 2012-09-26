# neubot/raw.py

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
 The main() of `neubot raw` subcommand.
'''

import getopt
import logging
import os
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.backend import BACKEND
from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.poller import POLLER
from neubot.raw_negotiate import RawNegotiate

from neubot import log
from neubot import privacy
from neubot import runner_clnt

def main(args):
    ''' Main function '''
    try:
        options, arguments = getopt.getopt(args[1:], '6A:np:vy')
    except getopt.error:
        sys.exit('usage: neubot raw [-6nvy] [-A address] [-p port]')
    if arguments:
        sys.exit('usage: neubot raw [-6nvy] [-A address] [-p port]')

    prefer_ipv6 = 0
    address = 'master.neubot.org'
    runner = 1
    port = 8080
    noisy = 0
    fakeprivacy = 0
    for name, value in options:
        if name == '-6':
            prefer_ipv6 = 1
        elif name == '-A':
            address = value
        elif name == '-n':
            runner = 0
        elif name == '-p':
            port = int(value)
        elif name == '-v':
            noisy = 1
        elif name == '-y':
            fakeprivacy = 1

    if os.path.isfile(DATABASE.path):
        DATABASE.connect()
        CONFIG.merge_database(DATABASE.connection())
    else:
        logging.warning('raw: database file is missing: %s', DATABASE.path)
        BACKEND.use_backend('null')
    if noisy:
        log.set_verbose()
    if runner:
        result = runner_clnt.runner_client(CONFIG['agent.api.address'],
          CONFIG['agent.api.port'], CONFIG['verbose'], 'raw')
        if result:
            sys.exit(0)

    logging.info('raw: running the test in the local process context...')
    if not fakeprivacy and not privacy.allowed_to_run():
        privacy.complain()
        logging.info('raw: otherwise use -y option to temporarily provide '
                     'privacy permissions')
        sys.exit(1)

    handler = RawNegotiate()
    handler.connect((address, port), prefer_ipv6, 0, {})
    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
