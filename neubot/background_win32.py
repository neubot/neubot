# neubot/background_win32.py

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

''' Run in background on Win32 '''

import getopt
import logging
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.backend import BACKEND
from neubot.background_rendezvous import BACKGROUND_RENDEZVOUS
from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.log import LOG
from neubot.poller import POLLER
from neubot.updater_win32 import UpdaterWin32

from neubot import background_api
from neubot import privacy
from neubot import utils_hier
from neubot import utils_version

def __start_updater():
    ''' Start updater '''
    updater = UpdaterWin32('win32', utils_hier.BASEDIR)
    updater.start()

def main(args):
    ''' Main() function '''

    try:
        options, arguments = getopt.getopt(args[1:], '')
    except getopt.error:
        sys.exit('usage: neubot background_win32')
    if options or arguments:
        sys.exit('usage: neubot background_win32')

    # Read settings from database
    CONFIG.merge_database(DATABASE.connection())

    BACKEND.use_backend("neubot")
    BACKEND.datadir_init()

    #
    # Save logs into the database, to easily access
    # and show them via the web user interface.
    #
    LOG.use_database()

    logging.info('%s for Windows: starting up', utils_version.PRODUCT)

    # Complain if privacy settings are not OK
    privacy.complain_if_needed()

    background_api.start_api()
    BACKGROUND_RENDEZVOUS.start()

    __start_updater()

    POLLER.loop()

    logging.info('%s for Windows: shutting down', utils_version.PRODUCT)
    LOG.writeback()

    #
    # Make sure that we do not leave the database
    # in an inconsistent state.
    #
    DATABASE.close()

if __name__ == '__main__':
    main(sys.argv)
