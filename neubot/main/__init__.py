# neubot/main/__init__.py

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

import os.path
import sys

if __name__ == "__main__":
    path = os.path.abspath(__file__)
    me = os.sep.join(["neubot", "main.py"])
    i = path.find(me)
    path = path[:i]
    sys.path.insert(0, path)

USAGE = '''\
neubot - The network neutrality bot

Usage: neubot
       neubot start [[ADDRESS] PORT]
       neubot status [[ADDRESS] PORT]
       neubot stop [[ADDRESS] PORT]
       neubot --help
       neubot -V
       neubot COMMAND [-ElvV] [-D PROPERTY[=VALUE]] [-f FILE]

Try `neubot help` to get a list of available subcommands.
Try `neubot COMMAND --help` for more help on COMMAND.
'''

VERSION = "0.4-rc6"

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

    if os.environ.get("NEUBOT_DEBUG", ""):
        from neubot import utils
        if utils.intify(os.environ["NEUBOT_DEBUG"]):
            sys.stderr.write("Running in debug mode\n")
            from neubot.debug import PROFILER
            sys.setprofile(PROFILER.notify_event)

    if os.environ.get("NEUBOT_MEMLEAK", ""):
        from neubot import utils
        if utils.intify(os.environ["NEUBOT_MEMLEAK"]):
            sys.stderr.write("Running in leak-detection mode\n")
            import gc
            gc.set_debug(gc.DEBUG_LEAK)

    # Quick argv classification

    if len(argv) == 1:
        start = True
        webgui = True

    elif len(argv) >= 2 and len(argv) < 5:
        command = argv[1]
        if command == "--help":
            sys.stdout.write(USAGE)
            sys.exit(0)
        elif command == "-V":
            sys.stdout.write(VERSION + "\n")
            sys.exit(0)
        elif command == "start":
            start = True
        elif command == "status":
            status = True
        elif command == "stop":
            stop = True
        else:
            slowpath = True

        if not slowpath and len(argv) >= 3:
            if len(argv) == 4:
                address = argv[2]
                port = argv[3]
            else:
                port = argv[2]

    else:
        slowpath = True

    # Slow / quick startup

    if slowpath:
        from neubot.main import module
        module.run(argv)

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
                response.read()
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
                from neubot import agent
                agent.main([argv[0], "-Dagent.api.port=%s" % port,
                             "-Dagent.api.address=%s" % address])
                sys.exit(0)

            # XXX
            if sys.platform == "darwin":
                os.environ["DISPLAY"] = "fake-neubot-display:0.0"

            if webgui and "DISPLAY" in os.environ:
                from neubot.main import browser
                browser.open_patient(address, port)

        elif os.name == "nt":

            if webgui:
                from neubot.main import browser

                if not running and start:
                    browser.open_patient(address, port, True)
                else:
                    browser.open_patient(address, port)

            if not running and start:
                from neubot import agent
                agent.main([argv[0]])

        else:
            sys.stderr.write("Your operating system is not supported\n")
            sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
