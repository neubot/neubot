# neubot/pathnames.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from neubot import log
from sys import exit
from sys import argv
import os.path

PREFIX = "@PREFIX@"
if PREFIX.startswith("@"):
    PREFIX = "/usr/local"

DIRS = []
DATABASE = ""
CONFIG = []
WWW = ""

if os.name == "nt":
    if not os.environ.has_key("APPDATA"):
        raise RuntimeError("os.environ['APPDATA'] does not exist")
    appdata = os.environ["APPDATA"]
    CONFIG.append(appdata + "\\neubot\\config")
    DATABASE = appdata + "\\neubot\\database.sqlite3"
    DIRS.append(appdata + "\\neubot")
    WWW = os.path.dirname(os.path.abspath(argv[0])) + "\\www"
else:
    # assume posix
    CONFIG.append("/etc/neubot/config")
    DIRS.append("/etc/neubot")
    DATABASE = "/var/neubot/database.sqlite3"
    DIRS.append("/var/neubot")
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
        DIRS.append(home + "/.neubot")
    WWW = PREFIX + "/share/neubot/www"

def printfiles():
    log.debug("Directories   : %s" % str(DIRS))
    log.debug("Config files  : %s" % str(CONFIG))
    log.debug("Database file : %s" % DATABASE)
    log.debug("WWW root      : %s" % WWW)

if __name__ == "__main__":
    log.verbose()
    printfiles()
