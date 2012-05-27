# neubot/browser.py

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

''' Open browser '''

import logging
import sys
import os
import re

if __name__ == '__main__':
    sys.path.insert(0, '.')

if os.name == 'nt':
    from neubot import browser_nt
    BROWSER_DRIVER = browser_nt
elif os.name == 'posix' and sys.platform == 'darwin':
    from neubot import browser_macos
    BROWSER_DRIVER = browser_macos
else:
    from neubot import browser_null
    BROWSER_DRIVER = browser_null

def open_browser(uri):
    ''' Open browser '''

    #
    # Be defensive and make sure that what the caller has passed us
    # looks like the URI of an HTML page.
    # If the URI looks good hand over the job to the installed browser
    # driver, which invokes the system browser and returns without
    # blocking this process.
    #

    if not re.match('^http://[a-z0-9./:]+\.html$', uri):
        logging.warning('browser: not the URI of an HTML page: %s', uri)
        return False

    return BROWSER_DRIVER.open_browser(uri)

def main(args):
    ''' Main function '''
    if len(args) == 1:
        args.append('http://127.0.0.1:9774/index.html')
    open_browser(args[1])

if __name__ == '__main__':
    main(sys.argv)
