# neubot/viewer.py

#
# Copyright (c) 2011, 2013
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

''' Neubot viewer '''

import getopt
import os
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import utils_hier
from neubot import utils_rc

def fallback_main(args):
    ''' Fallback main function '''
    try:
        getopt.getopt(args[1:], '')
    except getopt.error:
        sys.exit('usage: neubot viewer')

    if os.path.isfile(utils_hier.APIFILEPATH):
        config = utils_rc.parse_safe(utils_hier.APIFILEPATH)
    else:
        config = {}
    address = config.get('address', '127.0.0.1')
    port = config.get('port', 9774)

    sys.stderr.write('FATAL: python-webkit not available on this system.\n')
    sys.stderr.write('Hint: Web interface at <%s:%d>, use your browser.\n' % (
                     address, port))
    sys.exit(1)

try:
    from neubot.viewer_webkit_gtk import main
except ImportError:
    def main(args):
        ''' Main function '''
        fallback_main(args)

if __name__ == '__main__':
    main(sys.argv)
