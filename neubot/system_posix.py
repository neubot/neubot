# neubot/system_posix.py

#
# Copyright (c) 2010-2011
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

'''
 Code for UNIX
'''

# NB: This code is currently being refactored.

#
# When we MUST exit better to use os._exit() rather than
# sys.exit() because the former cannot be catched while
# the latter can.
#

UNPRIV_USER = '_neubot'

import os
import syslog

from neubot import utils_hier
from neubot import utils_posix
from neubot import utils_rc

def __logger(severity, message):

    ''' Log @message at the given @severity using syslog '''

    #
    # Implemented using syslog becuse SysLogHandler is
    # difficult to use: you need to know the path to the
    # system specific ``/dev/log``.
    #

    if severity == 'ERROR':
        syslog.syslog(syslog.LOG_ERR, message)
    elif severity == 'WARNING':
        syslog.syslog(syslog.LOG_WARNING, message)
    elif severity == 'DEBUG':
        syslog.syslog(syslog.LOG_DEBUG, message)
    else:
        syslog.syslog(syslog.LOG_INFO, message)

def get_background_logger():
    ''' Return the background logger '''
    syslog.openlog("neubot", syslog.LOG_PID, syslog.LOG_DAEMON)
    return __logger

def _get_profile_dir():
    ''' The profile directory is always LOCALSTATEDIR '''
    return utils_hier.LOCALSTATEDIR

def _want_rwx_dir(datadir):

    '''
     This function ensures that the unprivileged user is the
     owner of the directory that contains Neubot database.
     Otherwise sqlite3 fails to lock the database for writing
     (it creates a lockfile for that).

     Read more at http://www.neubot.org/node/14
    '''

    # Does the directory exist?
    if not os.path.isdir(datadir):
        os.mkdir(datadir, 493)          # 0755 in base 10

    # Change directory ownership
    if os.getuid() == 0:
        passwd = getpwnam()
        os.chown(datadir, passwd.pw_uid, passwd.pw_gid)

def go_background():
    ''' Detach from the shell and run in background '''
    utils_posix.daemonize(pidfile='/var/run/neubot.pid')

def getpwnam():
    ''' Wrapper for getpwnam '''
    cnf = utils_rc.parse_safe('/etc/neubot/users')
    unpriv_user = cnf.get('unpriv_user', UNPRIV_USER)
    passwd = utils_posix.getpwnam(unpriv_user)
    return passwd

def drop_privileges():
    '''
     Drop root privileges and run on behalf of the specified
     unprivileged users.
    '''
    passwd = getpwnam()
    utils_posix.chuser(passwd)

def _want_rw_file(path):

    '''
     Ensure that the given file is readable and writable
     by its owner.  If running as root force ownership
     to be of the unprivileged user.
    '''

    # Create file if non-existent
    filep = open(path, "ab+")
    filep.close()

    # Enforce file ownership
    if os.getuid() == 0:
        passwd = getpwnam()
        os.chown(path, passwd.pw_uid, passwd.pw_gid)

    # Set permissions
    os.chmod(path, 420)         # 0644 in base 10

def has_enough_privs():
    ''' Returns true if this process has enough privileges '''
    return os.getuid() == 0
