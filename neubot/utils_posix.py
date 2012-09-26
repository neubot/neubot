# neubot/utils_posix.py

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

''' POSIX utils '''

#
# Part of the POSIX code is in this file, part is in system, and part
# is in updater/unix.  The mid-term plan is to move here all the POSIX
# related code.
#

import errno
import getopt
import logging
import os.path
import pwd
import signal
import sys
import time

# For python3 portability
MODE_755 = int('755', 8)
MODE_644 = int('644', 8)
MODE_022 = int('022', 8)

def is_running(pid):
    ''' Returns true if PID is running '''
    running = True
    try:
        os.kill(pid, 0)
    except OSError:
        why = sys.exc_info()[1]
        if why[0] != errno.ESRCH:
            raise
        running = False
    return running

def terminate_process(pid):
    ''' Terminate process '''
    if not is_running(pid):
        logging.debug('utils_posix: process %d is not running', pid)
        return True
    logging.debug('utils_posix: sending %d the TERM signal', pid)
    os.kill(pid, signal.SIGTERM)
    time.sleep(1)
    if not is_running(pid):
        logging.debug('utils_posix: process %d terminated', pid)
        return True
    logging.debug('utils_posix: sending %d the KILL signal', pid)
    os.kill(pid, signal.SIGKILL)
    time.sleep(1)
    if not is_running(pid):
        logging.debug('utils_posix: process %d terminated', pid)
        return True
    return False

def detach(**kwargs):

    '''
     Perform the typical steps to become a daemon.

     In detail:

     1. detach from the current shell;

     2. become a session leader;

     3. detach from the current session;

     4. chdir to rootdir;

     5. redirect stdin, stdout, stderr to /dev/null;

     6. ignore SIGINT, SIGPIPE;

     7. write pidfile;

     8. install SIGTERM, SIGHUP handler.

    '''

    #
    # I've verified that the first chunk of this function matches loosely the
    # behavior of the daemon(3) function available under BSD.  What is missing
    # here is setlogin(2) which is not part of python standard library.
    #

    if kwargs.get('detach'):
        logging.debug('utils_posix: detach from current shell')
        if os.fork() > 0:
            os._exit(0)
        os.setsid()
        if os.fork() > 0:
            os._exit(0)

    if kwargs.get('close_stdio'):
        logging.debug('utils_posix: close stdio')
        for fdesc in range(3):
            os.close(fdesc)
        for _ in range(3):
            os.open('/dev/null', os.O_RDWR)

    if kwargs.get('chdir'):
        logging.debug('utils_posix: chdir() to "%s"', kwargs['chdir'])
        os.chdir(kwargs['chdir'])

    if kwargs.get('ignore_signals'):
        logging.debug('utils_posix: ignore SIGINT and SIGPIPE')
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)

    if kwargs.get('pidfile'):
        logging.debug('utils_posix: pidfile "%s"', kwargs['pidfile'])
        filep = open(kwargs['pidfile'], 'w')
        filep.write('%d\n' % os.getpid())
        filep.close()

    if kwargs.get('sighandler'):
        logging.debug('utils_posix: install signal handlers')
        signal.signal(signal.SIGTERM, kwargs['sighandler'])
        signal.signal(signal.SIGHUP, kwargs['sighandler'])

def chuser(passwd):

    '''
     Change user, group to `passwd.pw_uid`, `passwd.pw_gid` and setup a bare
     environement for the new user.  This function is mainly used to drop root
     privileges, but can also be used to sanitize the privileged daemon's
     environment.

     More in detail, this function will:

     1. set the umask to 022;

     2. change group ID to `passwd.pw_gid`;

     3. clear supplementary groups;

     4. change user ID to `passwd.pw_uid`;

     5. purify environment.

    '''

    #
    # I've checked that this function does more or less the same steps of
    # OpenBSD setusercontext(3) and of launchd(8) to drop privileges.
    # For dropping privileges we try to follow the guidelines established by
    # Chen, et al. in "Setuid Demystified":
    #
    # > Since setresuid has a clear semantics and is able to set each user ID
    # > individually, it should always be used if available.  Otherwise, to set
    # > only the effective uid, seteuid(new euid) should be used; to set all
    # > three user IDs, setreuid(new uid, new uid) should be used.
    #

    logging.debug('utils_posix: set umask 022')
    os.umask(MODE_022)

    logging.debug('utils_posix: change gid to %d', passwd.pw_gid)
    if hasattr(os, 'setresgid'):
        os.setresgid(passwd.pw_gid, passwd.pw_gid, passwd.pw_gid)
    elif hasattr(os, 'setregid'):
        os.setregid(passwd.pw_gid, passwd.pw_gid)
    else:
        raise RuntimeError('utils_posix: cannot drop group privileges')

    logging.debug('utils_posix: set minimal supplementary groups')
    os.setgroups([passwd.pw_gid])

    logging.debug('utils_posix: change uid to %d', passwd.pw_uid)
    if hasattr(os, 'setresuid'):
        os.setresuid(passwd.pw_uid, passwd.pw_uid, passwd.pw_uid)
    elif hasattr(os, 'setreuid'):
        os.setreuid(passwd.pw_uid, passwd.pw_uid)
    else:
        raise RuntimeError('utils_posix: cannot drop user privileges')

    logging.debug('utils_posix: purify environ')
    for name in list(os.environ.keys()):
        del os.environ[name]
    os.environ = {
                  "HOME": "/",
                  "LOGNAME": passwd.pw_name,
                  "PATH": "/usr/local/bin:/usr/bin:/bin",
                  "TMPDIR": "/tmp",
                  "USER": passwd.pw_name,
                 }

def getpwnam(uname):
    ''' Get password database entry by name '''
    # Wrapper that reports a better error message
    try:
        passwd = pwd.getpwnam(uname)
    except KeyError:
        raise RuntimeError('utils_posix: "%s": no such user' % uname)
    else:
        logging.debug('utils_posix: getpwnam(): %s/%d/%d', passwd.pw_name,
                      passwd.pw_uid, passwd.pw_gid)
        return passwd

def mkdir_idempotent(curpath, uid=None, gid=None):
    ''' Idempotent mkdir with 0755 permissions'''

    if not os.path.exists(curpath):
        os.mkdir(curpath, MODE_755)
    elif not os.path.isdir(curpath):
        raise RuntimeError('%s: Not a directory' % curpath)

    if uid is None:
        uid = os.getuid()
    if gid is None:
        gid = os.getgid()

    os.chown(curpath, uid, gid)
    os.chmod(curpath, MODE_755)

def touch_idempotent(curpath, uid=None, gid=None):
    ''' Idempotent touch with 0644 permissions '''

    if not os.path.exists(curpath):
        os.close(os.open(curpath, os.O_WRONLY|os.O_CREAT
                         |os.O_APPEND, MODE_644))
    elif not os.path.isfile(curpath):
        raise RuntimeError('%s: Not a file' % curpath)

    if uid is None:
        uid = os.getuid()
    if gid is None:
        gid = os.getgid()

    os.chown(curpath, uid, gid)
    os.chmod(curpath, MODE_644)

USAGE = '''\
Usage: utils_posix.py [-f pwd_field] [-g gid] [-u uid] command [args...]'''

def main(args):
    ''' main() function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'f:g:u:')
    except getopt.error:
        sys.exit(USAGE)

    gid = None
    selector = None
    uid = None
    for name, value in options:
        if name == '-f':
            selector = value
        elif name == '-g':
            gid = int(value)
        elif name == '-u':
            uid = int(value)

    if len(arguments) == 2 and arguments[0] == 'getpwnam':
        passwd = getpwnam(arguments[1])
        if selector:
            passwd = getattr(passwd, selector)
        sys.stdout.write('%s\n' % str(passwd))

    elif len(arguments) == 2 and arguments[0] == 'mkdir':
        mkdir_idempotent(arguments[1], uid, gid)

    elif len(arguments) == 2 and arguments[0] == 'touch':
        touch_idempotent(arguments[1], uid, gid)

    else:
        sys.exit(USAGE)

if __name__ == '__main__':
    main(sys.argv)
