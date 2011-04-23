# neubot/boot.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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

import getopt
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.log import LOG

VERSION = "0.3.6\n"

def write_help(fp, name, descr):
    fp.write('''\
Neubot %(name)s -- %(descr)s

Usage: neubot %(name)s [-Vv] [-D PROPERTY[=VALUE]] [-f FILE] [--help]

Options:
    -D PROPERTY[=VALUE]         : Set the VALUE of the property PROPERTY
    -f FILE                     : Use FILE instead of the default database
    --help                      : Print this help screen and exit
    -V                          : Print version number and exit
    -v                          : Run the program in verbose mode

''' % locals())

def common(name, descr, args):

    try:
        options, arguments = getopt.getopt(args[1:], "D:f:Vv", ["help"])
    except getopt.GetoptError:
        write_help(sys.stderr, name, descr)
        sys.exit(1)

    if arguments:
        write_help(sys.stderr, name, descr)
        sys.exit(1)

    for key, value in options:
        if key == "-D":
             # No shortcuts because it grows too confusing
             CONFIG.register_property(value)
        elif key == "-f":
             DATABASE.set_path(value)
        elif key == "--help":
             write_help(sys.stdout, name, descr)
             CONFIG.print_descriptions(sys.stdout)
             sys.exit(0)
        elif key == "-V":
             sys.stdout.write(VERSION)
             sys.exit(0)
        elif key == "-v":
             LOG.verbose()

    DATABASE.connect()

    CONFIG.merge_database(DATABASE.connection())
    CONFIG.merge_environ()
    CONFIG.merge_properties()

if __name__ == "__main__":
    common("cmdline", "Generic bootstrap code for Neubot commands", sys.argv)
    CONFIG.store_fp(sys.stdout)
