# neubot/shell.py

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

import os
import shlex
import sys
import textwrap
import re

# For raw_input()
try:
    import readline
except ImportError:
    pass

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.log import LOG

MODULES = {
    "agent"      : "agent",
    "database"   : "database",
    "bittorrent" : "bittorrent.main",
    "http"       : "http.client",
    "httpd"      : "http.server",
    "rendezvous" : "rendezvous",
    "speedtest"  : "speedtest",
    "statusicon" : "statusicon",
    "stream"     : "net.stream",
}

def docommand(argv):

    module = argv[0]
    MAIN = None

    if module == "help":
        sys.stdout.write("Neubot help -- prints available commands\n")

        commands = " ".join(sorted(MODULES.keys()))
        lines =  textwrap.wrap(commands, 60)
        sys.stdout.write("Commands: " + lines[0] + "\n")
        for s in lines[1:]:
            sys.stdout.write("          " + s + "\n")

        sys.stdout.write("Try `neubot COMMAND --help` for more help\n")
        return

#   Not yet
#   # run in interactive mode
#   if module == "-i":
#       main(["neubot"])
#       return

    if not module in MODULES:
        sys.stderr.write("Invalid module: %s\n" % module)
        sys.stderr.write("Try `neubot help` to see the available modules\n")
        return

    module = MODULES[module]

    argv[0] = "neubot " + argv[0]
    exec("from neubot.%s import main as MAIN" % module)
    MAIN(argv)
    del MAIN

def doreadline(fp):

    if not os.isatty(fp.fileno()):
        s = fp.readline()
        if not s:
            raise EOFError
    else:
        s = raw_input("> ")

    s = s.strip()
    if not s:
        return

    vector = shlex.split(s)
    if vector and vector[0] == "neubot":
        del vector[0]

    docommand(vector)

def main(argv, fp=sys.stdin):

    del argv[0]
    if argv:
        docommand(argv)
        return

    while True:
        try:
            doreadline(fp)
        except EOFError:
            break
        except (KeyboardInterrupt, SystemExit):
            print
        except:
            LOG.exception()

if __name__ == "__main__":
    main(sys.argv)
