# neubot/filesys_posix.py

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

''' POSIX filesystem '''

import getopt
import logging
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import utils_posix
from neubot import utils_path

# Default user name
UNAME = '_neubot'

class FileSystemPOSIX(object):
    ''' POSIX file system '''

    def __init__(self, uname=UNAME, datadir=None):
        ''' Init POSIX filesystem '''

        if datadir:
            self.datadir = datadir
        elif sys.platform.startswith('linux'):
            self.datadir = '/var/lib/neubot'
        else:
            self.datadir = '/var/neubot'
        logging.debug('filesys_posix: datadir: %s', self.datadir)

        logging.debug('filesys_posix: user name: %s', uname)
        self.passwd = utils_posix.getpwnam(uname)
        logging.debug('filesys_posix: uid: %d', self.passwd.pw_uid)
        logging.debug('filesys_posix: gid: %d', self.passwd.pw_gid)

    def datadir_init(self):
        ''' Initialize datadir '''
        #
        # Here we are assuming that /var (BSD) or /var/lib (Linux)
        # exists and has the correct permissions.
        # We are also assuming that we are running with enough privs
        # to be able to create a directory there on behalf of the
        # specified uid and gid.
        #
        logging.debug('filesys_posix: datadir init: %s', self.datadir)
        utils_posix.mkdir_idempotent(self.datadir, self.passwd.pw_uid,
                                     self.passwd.pw_gid)

    def datadir_touch(self, components):
        ''' Touch a file below datadir '''
        return utils_path.depth_visit(self.datadir, components, self._visit)

    def _visit(self, curpath, leaf):
        ''' Callback for depth_visit() '''
        if not leaf:
            logging.debug('filesys_posix: mkdir_idempotent: %s', curpath)
            utils_posix.mkdir_idempotent(curpath, self.passwd.pw_uid,
                                         self.passwd.pw_gid)
        else:
            logging.debug('filesys_posix: touch_idempotent: %s', curpath)
            utils_posix.touch_idempotent(curpath, self.passwd.pw_uid,
                                         self.passwd.pw_gid)

USAGE = 'Usage: filesys_posix.py [-d datadir] [-u user] component...'

def main(args):
    ''' main function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'd:u:v')
    except getopt.error:
        sys.exit(USAGE)
    if len(arguments) == 0:
        sys.exit(USAGE)

    datadir = None
    uname = UNAME
    for name, value in options:
        if name == '-d':
            datadir = value
        elif name == '-u':
            uname = value
        elif name == '-v':
            logging.getLogger().setLevel(logging.DEBUG)

    filesys = FileSystemPOSIX(uname, datadir)
    filesys.datadir_init()
    filesys.datadir_touch(arguments)

if __name__ == '__main__':
    main(sys.argv)
