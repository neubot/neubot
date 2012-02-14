# neubot/browser_null.py

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

''' Null open browser driver '''

import logging
import sys

def open_browser(uri):
    ''' Open browser on Windows NT '''

    #
    # The message here is a warning message because I do not expect
    # this null browser to ever be called outside of the typical testing
    # environment.  So better to see that on the logs.
    #

    logging.warning('browser_null: pretending to open: %s', uri)
    return True

def main(args):
    ''' Main function '''
    open_browser(args[1])

if __name__ == '__main__':
    main(sys.argv)
