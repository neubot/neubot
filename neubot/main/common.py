# neubot/main/common.py

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

#
# This implements a common main() that reads properties
# from command line, from the environment and from the
# database file.  Most if not all Neubot commands should
# use this common main in order to provide an uniform
# and predictable command line interface.
#

import getopt
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.database import DATABASE

from neubot import utils_version

VERSION = utils_version.CANONICAL_VERSION

def write_help(fp, name, descr):
    fp.write('''\
Neubot %(name)s -- %(descr)s

Usage: neubot %(name)s [-ElVv] [-D PROPERTY[=VALUE]] [-f FILE] [--help]

Options:
    -D PROPERTY[=VALUE] : Define the VALUE of the given PROPERTY
    -E                  : Ignore NEUBOT_OPTIONS environment variable
    -f FILE             : Force file name of the database to FILE
    --help              : Print this help screen and exit
    -l                  : List all the available properties and exit
    -V                  : Print version number and exit
    -v                  : Verbose: print much more log messages

''' % locals())

def main(name, descr, args):
    Eflag = False
    lflag = False

    try:
        options, arguments = getopt.getopt(args[1:], "D:Ef:lVv", ["help"])
    except getopt.GetoptError:
        write_help(sys.stderr, name, descr)
        sys.exit(1)

    if arguments:
        write_help(sys.stderr, name, descr)
        sys.exit(1)

    verbose = 0

    for key, value in options:
        if key == "-D":
            # No shortcuts because it grows too confusing
            CONFIG.register_property(value)
        elif key == "-E":
            Eflag = True
        elif key == "-f":
            DATABASE.set_path(value)
        elif key == "--help":
            write_help(sys.stdout, name, descr)
            sys.exit(0)
        elif key == "-l":
            lflag = True
        elif key == "-V":
            sys.stdout.write(VERSION + "\n")
            sys.exit(0)
        elif key == "-v":
            verbose = 1

    DATABASE.connect()

    CONFIG.merge_database(DATABASE.connection())
    if not Eflag:
        CONFIG.merge_environ()
    CONFIG.merge_properties()

    # Apply the setting after we've read database and environment
    if verbose:
        CONFIG['verbose'] = 1

    if lflag:
        CONFIG.print_descriptions(sys.stdout)
        sys.exit(0)

if __name__ == "__main__":
    main("common.main", "Common main() for all Neubot commands", sys.argv)
    CONFIG.store_fp(sys.stdout)
