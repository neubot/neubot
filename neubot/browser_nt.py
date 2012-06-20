# neubot/browser_nt.py

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

''' NT open browser driver '''

import asyncore
import logging
import sys
import os

def open_browser(uri):
    ''' Open browser on Windows NT '''

    #
    # We use the startfile() function here because we want to be dead
    # sure that the command is nonblocking and webbrowser focus more
    # on flexibility than on being nonblocking.
    # The only case where startfile() is going to fail is the one in
    # which a handler for HTML is not installed.
    #

    #
    # The check whether the URI actually looks like a URI is
    # performed in browser.py.  As an extra check, ensure that
    # we don't call startfile() when a file with that name exists
    # on the system.  I don't know the internals of startfile()
    # and I prefer to be paranoid.
    #
    if os.path.exists(uri):
        sys.stderr.write('ERROR: there is a file named like the URI\n')
        return False

    try:
        os.startfile(uri)
    except WindowsError:
        error = str(asyncore.compact_traceback())
        logging.warning('browser_nt: startfile() failed: %s', error)
        return False

    return True

def main(args):
    ''' Main function '''
    open_browser(args[1])

if __name__ == '__main__':
    main(sys.argv)
