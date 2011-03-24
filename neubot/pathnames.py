# neubot/pathnames.py

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
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

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from neubot.log import LOG
from neubot.system import ismacosx
from sys import exit
from sys import argv
import os.path

if os.name == "posix":
    from neubot.utils import getpwnamlx

PREFIX = "@PREFIX@"
if PREFIX.startswith("@"):
    PREFIX = "/usr/local"

DATABASE = ""
CONFIG = []

userdirs = []
sysdirs = []

if os.name == "nt":
    if not os.environ.has_key("APPDATA"):
        raise RuntimeError("os.environ['APPDATA'] does not exist")
    appdata = os.environ["APPDATA"]
    CONFIG.append(appdata + "\\neubot\\config")
    DATABASE = appdata + "\\neubot\\database.sqlite3"
    userdirs.append(appdata + "\\neubot")
else:
    # assume posix
    CONFIG.append("/etc/neubot/config")
    sysdirs.append("/etc/neubot")
    DATABASE = "/var/neubot/database.sqlite3"
    sysdirs.append("/var/neubot")
    #
    # Do NOT consider HOME when running as root because
    # this might cause issues when running e.g. sudo neubot
    # and the current user has a neubot configuration file
    # in $HOME.
    #
    if os.environ.has_key("HOME") and os.getuid() > 0:
        home = os.environ["HOME"]
        CONFIG.append(home + "/.neubot/config")
        DATABASE = home + "/.neubot/database.sqlite3"
        userdirs.append(home + "/.neubot")
    # We provide an App for MacOS X
    if ismacosx():
        progname = os.path.abspath(argv[0])
        prefix = progname.replace("/bin/neubot", "")

def printfiles():
    LOG.debug("Config files  : %s" % str(CONFIG))
    LOG.debug("Database file : %s" % DATABASE)

def _makedirs(dirs, perms=0755):
    for directory in dirs:
        if not os.path.exists(directory):
            LOG.info("* Create directory: %s" % directory)
            os.mkdir(directory, perms)

#
# We need to be the owner of /var/neubot because otherwise
# sqlite3 fails to lock the database for writing.
#
# Read more at http://www.neubot.org/node/14
#
def _adjust_ownership():
    passwd = getpwnamlx()
    os.chown("/var/neubot", passwd.pw_uid, passwd.pw_gid)

def checkdirs():
    if os.name == "posix" and os.getuid() == 0:
        _makedirs(sysdirs)
        _adjust_ownership()
    _makedirs(userdirs)

if __name__ == "__main__":
    LOG.verbose()
    printfiles()
