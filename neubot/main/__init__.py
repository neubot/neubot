#!/usr/bin/env python

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
import logging

if __name__ == "__main__":
    # Magic!
    sys.path.insert(0, os.path.dirname (os.path.dirname(os.path.dirname
                                        (os.path.abspath(__file__)))))

from neubot import utils_version

USAGE = '''\
neubot - The network neutrality bot

Usage: neubot
       neubot --help
       neubot -V
       neubot subcommand ...

Try `neubot help` to get a list of available subcommands.
Try `neubot subcommand --help` for more help on subcommand.
'''

VERSION = utils_version.CANONICAL_VERSION

def main(argv):

    slowpath = False
    webgui = False
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

    # Hook for Neubot for MacOSX
    if os.name == 'posix' and sys.platform == 'darwin':
        from neubot import main_macos
        main_macos.main(argv)
        return

    # Quick argv classification

    if len(argv) == 1:
        start = True
        webgui = True

    elif len(argv) == 2:
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

                connection = httplib.HTTPConnection("127.0.0.1", "9774")
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

                connection = httplib.HTTPConnection("127.0.0.1", "9774")
                connection.request("POST", "/api/exit")

                # New /api/exit does not send any response
                #response = connection.getresponse()

                connection.close()

            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                logging.error('Exception', exc_info=1)
                sys.exit(1)

        # start / webbrowser

        if os.name == "posix":

            #
            # Fork off a child and use it to start the
            # Neubot agent.  The parent process will
            # open the browser, if needed.  Otherwise
            # it will exit.
            #
            if not running and start:
                if os.fork() == 0:
                    from neubot import agent
                    arguments = [ argv[0] ]
                    agent.main(arguments)
                    sys.exit(0)

            #
            # It's not wise at all to open the browser when
            # we are running as root.  Assume that when we
            # are root the user wants just to start the agent.
            #
            if webgui and "DISPLAY" in os.environ:
                if os.getuid() != 0:
                    from neubot.main import browser
                    browser.open_patient("127.0.0.1", "9774")

        elif os.name == "nt":

            if webgui:
                from neubot.main import browser

                if not running and start:
                    browser.open_patient("127.0.0.1", "9774", True)
                else:
                    browser.open_patient("127.0.0.1", "9774")

            if not running and start:
                from neubot import agent
                agent.main([argv[0]])

        else:
            sys.stderr.write("Your operating system is not supported\n")
            sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)
