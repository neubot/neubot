# neubot/system/win32.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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

''' Win32 system routines '''

# NB: This code is currently being refactored.

import os.path

from neubot import utils_sysdirs

def change_dir():
    ''' Change directory '''

def _get_profile_dir():
    ''' Get database directory '''
    return utils_sysdirs.LOCALSTATEDIR

def _want_rwx_dir(pathname):
    ''' Ensure the directory has RWX perms '''
    if not os.path.isdir(pathname):
        os.mkdir(pathname, 0755)

def go_background():
    ''' Run in background '''

def drop_privileges():
    ''' Drop root privileges '''

def redirect_to_dev_null():
    ''' Redirect stdio to /dev/null '''

def _want_rw_file(path):
    ''' Ensure the file has RW perms '''
    filep = open(path, "ab+")
    filep.close()

def _get_pidfile_dir():
    ''' Return directory where to write pidfile '''

#
# We tried NT Event Logger but it is not as friendly as
# syslog under Unix.  So we decided to write logs on the
# database only for Windows.
#
def __logger(severity, message):
    ''' Pretend to log a message '''

def get_background_logger():
    ''' Return the background logger '''
    return __logger
