# neubot/utils_nt.py

#
# Copyright (c) 2013
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

""" NT utils """

import os

# For python3 portability
MODE_755 = int('755', 8)
MODE_644 = int('644', 8)

class PWEntry(object):
    """ Fake password database entry """
    pw_uid = 0
    pw_gid = 0

def getpwnam(uname):
    """ Get password database entry by name """
    return PWEntry()

#
# I copied the following two functions from utils_posix.py, and I
# also commented out the code that couldn't run on Windows NT.
#

def mkdir_idempotent(curpath, uid=None, gid=None):
    ''' Idempotent mkdir with 0755 permissions'''

    if not os.path.exists(curpath):
        os.mkdir(curpath, MODE_755)
    elif not os.path.isdir(curpath):
        raise RuntimeError('%s: Not a directory' % curpath)

#   if uid is None:
#       uid = os.getuid()
#   if gid is None:
#       gid = os.getgid()

#   os.chown(curpath, uid, gid)
    os.chmod(curpath, MODE_755)

def touch_idempotent(curpath, uid=None, gid=None):
    ''' Idempotent touch with 0644 permissions '''

    if not os.path.exists(curpath):
#       os.close(os.open(curpath, os.O_WRONLY|os.O_CREAT
#                        |os.O_APPEND, MODE_644))
        filep = open(curpath, "w")
        filep.close()
    elif not os.path.isfile(curpath):
        raise RuntimeError('%s: Not a file' % curpath)

#   if uid is None:
#       uid = os.getuid()
#   if gid is None:
#       gid = os.getgid()

#   os.chown(curpath, uid, gid)
    os.chmod(curpath, MODE_644)
