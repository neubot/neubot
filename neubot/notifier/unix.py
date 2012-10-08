# neubot/notifier/unix.py

#
# Copyright (c) 2011 Marco Scopesi <marco.scopesi@gmail.com>,
#  Politecnico di Torino
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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
 This script is started when the user logs in into Gnome and
 periodically checks the status of the Neubot daemon, printing
 notifications if needed.
'''

import asyncore
import getopt
import json
import os.path
import sqlite3
import sys
import syslog
import time

if sys.version_info[0] == 3:
    import http.client as lib_http
else:
    import httplib as lib_http

try:
    import pynotify
except ImportError:
    sys.exit('Notifier support not available')

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import utils_hier
from neubot import privacy
from neubot import utils_version

NEUBOT_ICON = '@DATADIR@/icons/hicolor/scalable/apps/neubot.svg'
if not os.path.isfile(NEUBOT_ICON) or not os.access(NEUBOT_ICON, os.R_OK):
    NEUBOT_ICON = None

PRIVACY_TITLE = 'Neubot | No privacy settings'
PRIVACY_EXPLANATION = \
'Neubot is disabled because you have not provided the permission to save ' \
'and publish your Internet address.  To provide them, use Neubot GUI or ' \
'use (as root) the `neubot privacy` command on the command line.'

SHORT_PRIVACY_INTERVAL = 30
LONG_PRIVACY_INTERVAL = 3600

def __should_adjust_privacy(database_path):

    ''' Connect to the daemon, get privacy settings and return
        true if the user should adjust privacy settings '''

    try:

        address, port = '127.0.0.1', '9774'

        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM config;')
        for name, value in cursor:
            if name == 'agent.api.address':
                address = value
            elif name == 'agent.api.port':
                port = value
        connection.close()

        connection = lib_http.HTTPConnection(address, port)
        connection.request('GET', '/api/config')

        response = connection.getresponse()
        if response.status != 200:
            raise RuntimeError('Invalid response code: %d' % response.status)

        body = response.read()
        connection.close()

        dictionary = json.loads(body)
        if privacy.count_valid(dictionary, 'privacy.') != 3:
            # Should adjust settings
            return True

    except SystemExit:
        raise
    except:
        syslog.syslog(syslog.LOG_ERR, '%s' %
          str(asyncore.compact_traceback()))

    # No need to adjust settings
    return False

def __notify_adjust_privacy():

    ''' Notify the user she should adjust privacy settings
        via the web user interface '''

    try:
        pynotify.init(utils_version.PRODUCT)
        notification = pynotify.Notification(
                                             PRIVACY_TITLE,
                                             PRIVACY_EXPLANATION,
                                             NEUBOT_ICON
                                            )

        notification.set_urgency(pynotify.URGENCY_CRITICAL)
        notification.set_timeout(15)
        notification.show()
    except:
        syslog.syslog(syslog.LOG_ERR, '%s' %
          str(asyncore.compact_traceback()))

        #
        # Reraise the exception because each login spawns a new instance
        # of this script.  Old instances will fail because pynotify cannot
        # connect to the session dbus.  So, reraising the exception here
        # is a cheap and dirty way to enforce the singleton pattern.
        #
        raise

def main(args):

    ''' Notify the user '''

    try:
        options, arguments = getopt.getopt(args[1:], 'f:')
    except getopt.error:
        sys.exit('Usage: neubot notifier [-f database]\n')
    if arguments:
        sys.exit('Usage: neubot notifier [-f database]\n')

    database = utils_hier.DATABASEPATH
    for name, value in options:
        if name == '-f':
            database = value

    syslog.openlog('neubot_notify', syslog.LOG_PID, syslog.LOG_USER)

    while True:
        if __should_adjust_privacy(database):
            __notify_adjust_privacy()
            privacy_interval = SHORT_PRIVACY_INTERVAL
        else:
            privacy_interval = LONG_PRIVACY_INTERVAL

        time.sleep(privacy_interval)

if __name__ == '__main__':
    main(sys.argv)
