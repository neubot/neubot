# neubot/database_xxx.py

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

''' Database quirks '''

import logging
import os
import sys

def linux_fixup_databasedir():
    ''' Under Linux move database from /var/neubot to /var/lib/neubot '''
    # Explanation: /var/lib/neubot is FHS, /var/neubot isn't

    if os.name != 'posix':
        return
    if not sys.platform.startswith('linux'):
        return
    if os.getuid() != 0:
        return

    if not os.path.isfile('/var/neubot/database.sqlite3'):
        return
    if os.path.exists('/var/lib/neubot/database.sqlite3'):
        return

    logging.debug('database_xxx: /var/neubot -> /var/lib/neubot...')

    # Lazy import
    from neubot import utils_posix

    #
    # Here we create the new link as root, and we assume that
    # the caller will fix permissions afterwards.  This should
    # happen as long as we are invoked before the database
    # function that checks database path.
    #
    utils_posix.mkdir_idempotent('/var/lib/neubot')
    os.link('/var/neubot/database.sqlite3', '/var/lib/neubot/database.sqlite3')
    os.unlink('/var/neubot/database.sqlite3')

    logging.debug('database_xxx: /var/neubot -> /var/lib/neubot... done')
