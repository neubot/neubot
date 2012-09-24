# neubot/main/module.py

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

import sys
import textwrap
import logging

#
# XXX It would be nice to run just main() in MOD.__init__
# but let's not daydream: this is not going to happen for a
# heck of a long time.
#
MODULES = {
    "CA"                  : "net.CA",
    "agent"               : "agent",
    "api.client"          : "api.client",
    "database"            : "database.main",
    "bittorrent"          : "bittorrent",
    "http.client"         : "http.client",
    "http.server"         : "http.server",
    'notifier'            : 'notifier',
    "privacy"             : "privacy",
    "rendezvous.server"   : "rendezvous.server",
    "server"              : "server",
    "speedtest"           : "speedtest.client",
    "speedtest.client"    : "speedtest.client",
    "speedtest.negotiate" : "speedtest.negotiate",
    "speedtest.server"    : "speedtest.server",
    "stream"              : "net.stream",
    'viewer'              : 'viewer',
}

#
# XXX Good morning, this is an hack: py2exe does not
# load modules that are not referenced and we're very
# lazy in this file.  As a workaround let's load all
# modules when we're in windows and we are not frozen
# so we should reference all modules when py2exe is
# inspecting us.
#
if sys.platform == 'win32' and not hasattr(sys, 'frozen'):
    #import neubot.net.CA               # posix only
    import neubot.agent
    import neubot.api.client
    import neubot.database.main
    import neubot.bittorrent
    import neubot.http.client
    import neubot.http.server
    import neubot.privacy
    #import neubot.rendezvous.server    # requires PyGeoIP
    #import neubot.server               # ditto
    import neubot.speedtest.client
    import neubot.speedtest.client
    import neubot.speedtest.negotiate
    import neubot.speedtest.server
    import neubot.net.stream

def run(argv):

    # /usr/bin/neubot module ...
    del argv[0]
    module = argv[0]

    if module == "help":
        sys.stdout.write("Neubot help -- prints available commands\n")

        commands = " ".join(sorted(MODULES.keys()))
        lines =  textwrap.wrap(commands, 60)
        sys.stdout.write("Commands: " + lines[0] + "\n")
        for s in lines[1:]:
            sys.stdout.write("          " + s + "\n")

        sys.stdout.write("Try `neubot CMD --help` for more help on CMD.\n")
        sys.exit(0)

    if not module in MODULES:
        sys.stderr.write("Invalid module: %s\n" % module)
        sys.stderr.write("Try `neubot help` to list the available modules\n")
        sys.exit(1)

    # Dinamically load the selected module's main() at runtime
    module = "neubot.%s" % MODULES[module]
    __import__(module)
    MAIN = sys.modules[module].main

    # neubot module ...
    argv[0] = "neubot " + argv[0]

    try:
        MAIN(argv)
    except KeyboardInterrupt:
        pass
    except SystemExit:
        raise
    except:
        logging.error('Exception', exc_info=1)
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    run(sys.argv)
