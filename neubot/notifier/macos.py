# neubot/notifier/macos.py

#
# Copyright (c) 2011 Marco Scopesi <marco.scopesi@gmail.com>,
#  Politecnico di Torino
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

''' Notifier for MacOSX '''

# Adapted from neubot/notifier/unix.py

import asyncore
import getopt
import httplib
import json
import os.path
import sqlite3
import sys
import syslog
import time

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import privacy
from neubot import utils_hier
from neubot import utils_net

def __should_adjust_privacy(database_path):

    ''' Connect to the daemon, get privacy settings and return
        true if the user should adjust privacy settings '''

    #
    # Portions of this function can be shared between this
    # notifier and the UNIX one.  At the moment there's a
    # small amount of code duplication.
    #

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

        connection = httplib.HTTPConnection(address, port)
        connection.request('GET', '/api/config')

        response = connection.getresponse()
        if response.status != 200:
            raise RuntimeError('Invalid response code: %d' % response.status)

        body = response.read()
        connection.close()

        dictionary = json.loads(body)
        if privacy.count_valid(dictionary, 'privacy.') != 3:
            # Should adjust settings
            return "http://%s/" % utils_net.format_epnt((address, port))

    except SystemExit:
        raise
    except:
        syslog.syslog(syslog.LOG_ERR, '%s' %
          str(asyncore.compact_traceback()))

    # No need to adjust settings
    return None

def __notify_adjust_privacy(uri):

    ''' Notify the user she should adjust privacy settings
        via the web user interface '''

    #
    # For now just open the URI in the browser as we already do
    # under Windows.  I know that this sucks and I have plans to
    # send notifications e.g. via growl.
    #

    os.execv('/usr/bin/open', ['/usr/bin/open', uri])

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

    # Give Neubot time to start
    time.sleep(15)

    uri = __should_adjust_privacy(database)
    if uri:
        __notify_adjust_privacy(uri)

if __name__ == '__main__':
    main(sys.argv)
