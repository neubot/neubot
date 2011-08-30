# neubot/system/unix.py

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

'''
 Code for UNIX
'''

import pwd
import os.path
import signal
import syslog
import sys

class BackgroundLogger(object):

    '''
     We don't use logging.handlers.SysLogHandler because that class
     does not know the name of the UNIX domain socket in use for the
     current operating system.  In many Unices the UNIX domain socket
     name is /dev/log, but this is not true, for example, under the
     Mac.  A better solution seems to use syslog because this is just
     a wrapper to the host syslog library.  And who wrote such lib
     for sure knows the UNIX domain socket location for the current
     operating system.
    '''

    def __init__(self):
        ''' Initialize Unix background logger '''

        syslog.openlog("neubot", syslog.LOG_PID, syslog.LOG_DAEMON)

        self.error = lambda msg: syslog.syslog(syslog.LOG_ERR, msg)
        self.warning = lambda msg: syslog.syslog(syslog.LOG_WARNING, msg)
        self.info = lambda msg: syslog.syslog(syslog.LOG_INFO, msg)
        self.debug = lambda msg: syslog.syslog(syslog.LOG_DEBUG, msg)

def lookup_user_info(uname):

    '''
     Lookup and return the specified user's uid and gid.
     This function is not part of the function that changes
     user context because you may want to chroot() before
     dropping root privileges.
    '''

    try:
        return pwd.getpwnam(uname)
    except KeyError:
        syslog.syslog(syslog.LOG_ERR, 'No such "%s" user.  Exiting' % uname)
        sys.exit(1)

def _get_profile_dir():

    '''
     If we're running as an ordinary user, the profile directory
     is ``$HOME/.neubot``, otherwise it is ``/var/neubot``.
    '''

    if os.getuid() != 0:
        homedir = os.environ["HOME"]
        profiledir = os.sep.join([homedir, ".neubot"])
    else:
        profiledir = "/var/neubot"
    return profiledir

def change_dir():
    ''' Switch from current directory to root directory '''
    os.chdir("/")

def _want_rwx_dir(datadir, perror=None):

    '''
     This function ensures that the user ``_neubot`` is the
     owner of the directory that contains Neubot database.
     Otherwise sqlite3 fails to lock the database for writing
     (it creates a lockfile for that).

     Read more at http://www.neubot.org/node/14
    '''

    # Does the directory exist?
    if not os.path.isdir(datadir):
        os.mkdir(datadir, 0755)

    # Change directory ownership
    if os.getuid() == 0:
        passwd = lookup_user_info('_neubot')
        os.chown(datadir, passwd.pw_uid, passwd.pw_gid)

def go_background():
    ''' Detach from the shell and run in background '''

    # Ignore SIGINT
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Detach from the current shell
    if os.fork() > 0:
        sys.exit(0)

    # Create a new session
    os.setsid()

    # Detach from the new session
    if os.fork() > 0:
        sys.exit(0)

def drop_privileges(perror=None):

    '''
     Drop root privileges and run on behalf of the ``_neubot``
     unprivileged users.
    '''

    if os.getuid() == 0:
        passwd = lookup_user_info('_neubot')
        os.setgid(passwd.pw_gid)
        os.setuid(passwd.pw_uid)

def redirect_to_dev_null():

    ''' Redirect stdin, stdout and stderr to /dev/null '''

    for filedesc in range(3):
        os.close(filedesc)

    os.open("/dev/null", os.O_RDWR)
    os.open("/dev/null", os.O_RDWR)
    os.open("/dev/null", os.O_RDWR)

def _want_rw_file(path, perror=None):

    '''
     Ensure that the given file is readable and writable
     by its owner.  If running as root force ownership
     to be of the unprivileged ``_neubot`` user.
    '''

    # Create file if non-existent
    filep = open(path, "ab+")
    filep.close()

    # Enforce file ownership
    if os.getuid() == 0:
        passwd = lookup_user_info('_neubot')
        os.chown(path, passwd.pw_uid, passwd.pw_gid)

    # Set permissions
    os.chmod(path, 0644)

def _get_pidfile_dir():

    '''
     This function returns the directory where the pidfile is to
     be written or None if the user is not privileged.
    '''

    if os.getuid() == 0:
        return "/var/run"
    else:
        return None
