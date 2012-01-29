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

import getopt
import os.path
import pwd
import sys

# For python3 portability
MODE_755 = int('755', 8)
MODE_644 = int('644', 8)

def getpwnam(uname):
    ''' Get password database entry by name '''
    # Wrapper that reports a better error message
    try:
        return pwd.getpwnam(uname)
    except KeyError:
        raise RuntimeError('utils_posix: "%s": no such user' % uname)

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
