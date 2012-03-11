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
import os
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.background_rendezvous import BACKGROUND_RENDEZVOUS
from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.log import LOG
from neubot.poller import POLLER
from neubot.rootdir import ROOTDIR
from neubot.updater_win32 import UpdaterWin32

from neubot import background_api
from neubot import privacy

# We will install new versions in this directory
BASEDIR = os.path.dirname(ROOTDIR)

def __start_updater():
    ''' Start updater '''
    updater = UpdaterWin32('win32', BASEDIR)
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

    #
    # When we run as an agent we also save logs into
    # the database, to easily access and show them via
    # the web user interface.
    #
    LOG.use_database()

    # Complain if privacy settings are not OK
    privacy.complain_if_needed()

    background_api.start('127.0.0.1', '9774')
    BACKGROUND_RENDEZVOUS.start()

    __start_updater()

    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
