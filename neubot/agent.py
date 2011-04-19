# neubot/agent.py

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
import random
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.http.server import ServerHTTP
from neubot.api.server import ServerAPI
from neubot.rendezvous import RendezvousClient
from neubot.options import OptionParser
from neubot.net.poller import POLLER
from neubot.rootdir import WWW
from neubot.log import LOG
from neubot import system

# renames pending
from neubot.database import database as DATABASE

USAGE = """Neubot agent -- Run in background, periodically run tests

Usage: neubot agent [-Vv] [-D OPTION[=VALUE]] [-f FILE] [--help]

Options:
    -D OPTION[=VALUE]  : Set the VALUE of the option OPTION
    -f FILE            : Read options from file FILE
    --help             : Print this help screen and exit
    -V                 : Print version number and exit
    -v                 : Run the program in verbose mode

Macros  (defaults in square brackets):
    -D address=ADDRESS : ADDRESS of the local API server     [127.0.0.1]
    -D api=BOOL        : Enable/disable the local API server [True]
    -D daemonize=BOOL  : Run in background as a daemon       [True]
    -D interval=N      : Seconds between each rendezvous     [see below]
    -D master=MASTER   : Master-server FQDN                  [master.neubot.org]
    -D port=PORT       : PORT of the local API server        [9774]
    -D rendezvous=BOOL : Enable/disable rendezvous module    [True]

If you don't specify the interval Neubot will extract a random value
within a reasonable interval.
"""

VERSION = "Neubot 0.3.6\n"

def main(args):

    conf = OptionParser()
    conf.set_option("agent", "address", "127.0.0.1")
    conf.set_option("agent", "api", "True")
    conf.set_option("agent", "daemonize", "True")
    conf.set_option("agent", "interval", "0")
    conf.set_option("agent", "master", "master.neubot.org")
    conf.set_option("agent", "port", "9774")
    conf.set_option("agent", "rendezvous", "True")

    try:
        options, arguments = getopt.getopt(args[1:], "D:f:Vv", ["help"])
    except getopt.GetoptError:
        sys.stderr.write(USAGE)
        sys.exit(1)

    if len(arguments) != 0:
        sys.stderr.write(USAGE)
        sys.exit(1)

    for name, value in options:
        if name == "-D":
             conf.register_opt(value, "agent")
             continue
        if name == "-f":
             conf.register_file(value)
             continue
        if name == "--help":
             sys.stdout.write(USAGE)
             sys.exit(0)
        if name == "-V":
             sys.stdout.write(VERSION)
             sys.exit(0)
        if name == "-v":
             LOG.verbose()
             continue

    conf.merge_files()
    conf.merge_environ()
    conf.merge_opts()

    address = conf.get_option("agent", "address")
    api = conf.get_option_bool("agent", "api")
    daemonize = conf.get_option_bool("agent", "daemonize")
    interval = conf.get_option_uint("agent", "interval")
    master = conf.get_option("agent", "master")
    port = conf.get_option_uint("agent", "port")
    rendezvous = conf.get_option_bool("agent", "rendezvous")

    if not interval:
        interval = 1380 + random.randrange(0, 240)

    uri = "http://%s:9773/rendezvous" % master

    if api:
        server = ServerHTTP(POLLER)
        server.configure({"rootdir": WWW, "ssi": True})
        server.register_child(ServerAPI(POLLER), "/api")
        server.listen((address, port))

    DATABASE.start()

    if daemonize:
        system.change_dir()
        system.go_background()
        LOG.redirect()

    system.drop_privileges()

    if rendezvous:
        client = RendezvousClient(POLLER)
        client.init(uri, interval, False, False)
        client.rendezvous()

    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
