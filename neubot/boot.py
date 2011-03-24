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

#
# We rely on lazy import to keep this script's delay as near
# to zero as possible.  It's not acceptable for the user to wait
# for several milliseconds just to get the help message or the
# version number.
# This idea was initially proposed by Roberto D'Auria during
# an XMPP chat session.
#

import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

BOOLEANS = {
    "false": False,
    "0": False,
    "no": False,
    "off": False
}

USAGE = '''\
neubot - The network neutrality bot

Usage: neubot [command] [-vV] [-D macro[=value]] [-f file] [args...]
       neubot start
       neubot status
       neubot stop
       neubot --help|-h
       neubot -V
       neubot help
       neubot

Without arguments, starts the daemon in background, if needed, and,
then, opens the web user interface, using 127.0.0.1 as address and 9774
as port.

Run `neubot help` to get more extended help.
'''

VERSION = "Neubot 0.3.6\n"

def main(argv):

    address = "127.0.0.1"
    slowpath = False
    webgui = False
    port = "9774"
    start = False
    status = False
    stop = False

    if sys.version_info[0] > 2 or sys.version_info[1] < 5:
        sys.stderr.write("fatal: wrong Python version\n")
        sys.stderr.write("please run neubot using Python >= 2.5 and < 3.0\n")
        sys.exit(1)

    if BOOLEANS.get(os.environ.get("NEUBOT_DEBUG", "off").lower(), True):
        sys.stderr.write("Running in debug mode\n")
        from neubot import debug
        sys.setprofile(debug.trace)

    # Quick argv classification

    if len(argv) == 1:
        start = True
        webgui = True

#   Not yet
#   elif len(argv) >= 2 and len(argv) < 5:

    elif len(argv) == 2:
        command = argv[1]
        if command == "--help" or command == "-h":
            sys.stdout.write(USAGE)
            sys.exit(0)
        elif command == "-V":
            sys.stdout.write(VERSION)
            sys.exit(0)
        elif command == "start":
            start = True
        elif command == "status":
            status = True
        elif command == "stop":
            stop = True
        else:
            slowpath = True

#       Not yet
#       if not slowpath and len(argv) >= 3:
#            if len(argv) == 4:
#                address = argv[2]
#                port = argv[3]
#            else:
#                port = argv[2]

    else:
        slowpath = True

    # Slow / quick startup

    if slowpath:
        from neubot import shell
        shell.main(argv)

    else:
        running = False

        # Running?
        if start or status or stop:
            try:
                import httplib

                connection = httplib.HTTPConnection(address, port)
                connection.request("GET", "/api/version")
                response = connection.getresponse()
                if response.status == 200:
                    running = True
                connection.close()

            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                pass

        if status:
            if not running:
                sys.stdout.write("Not running\n")
            else:
                sys.stdout.write("Running\n")
            sys.exit(0)

        if running and start:
            sys.stdout.write("Already running\n")
        if not running and stop:
            sys.stdout.write("Not running\n")

        # Stop
        if running and stop:
            try:

                connection = httplib.HTTPConnection(address, port)
                connection.request("POST", "/api/exit")
                response = connection.getresponse()
                connection.close()

            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                from neubot.log import LOG
                LOG.exception()
                sys.exit(1)

        # start / webbrowser

        if os.name == "posix":

            if not running and start and os.fork() == 0:
                from neubot import rendezvous
                rendezvous.main([argv[0]])
                sys.exit(0)

            # XXX
            if sys.platform == "darwin":
                os.environ["DISPLAY"] = "fake-neubot-display:0.0"

            if webgui and "DISPLAY" in os.environ:
                import webbrowser
                sys.stderr.write("Opening Neubot web gui\n")
                webbrowser.open("http://%s:%s/" % (address, port))

        elif os.name == "nt":

            if webgui:
                import webbrowser

                func = lambda: \
		  webbrowser.open("http://%s:%s/" % (address, port))

                if not running and start:
                    import threading

                    t = threading.Thread(target=func)
                    sys.stderr.write("Opening Neubot web gui\n")
                    t.daemon = True
                    t.start()
                else:
                    sys.stderr.write("Opening Neubot web gui\n")
                    func()

            if not running and start:
                from neubot import rendezvous
                rendezvous.main([argv[0]])

        else:
            sys.stderr.write("Your operating system is not supported\n")
            sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
