# neubot/main.py
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

#
# Main function.
# Dispatch control to the module passed as the first
# argument or fallback to a safe default.
#

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from neubot import debug
from sys import setprofile
from neubot import pathnames
from neubot import log
from sys import stderr
from sys import stdout
from sys import argv
from sys import exit

# cheating a bit
from neubot.http import clients as http
from neubot.http import servers as httpd

from neubot import database
from neubot import rendezvous
from neubot import speedtest
from neubot import ui

import textwrap
import os.path

#
# Internal commands
#

def dohelp(args, fp=stdout):
     fp.write("Available commands: ")
     commands = " ".join(sorted(TABLE.keys()))
     lines = textwrap.wrap(commands, 50)
     fp.write("%s\n" % lines[0])
     for line in lines[1:]:
         fp.write("%s%s\n" % (" " * 20, line))
     fp.write("Try `neubot COMMAND --help' for more help on COMMAND\n")

def dostart(args):
    if len(args) == 2 and args[1] == "--help":
        stdout.write("Start the background neubot instance.\n")
        stdout.write("Usage: %s\n" % args[0])
        exit(0)
    if len(args) > 1:
        stderr.write("Usage: %s\n" % args[0])
        exit(1)
    conf = ui.UIConfig()
    conf.read(pathnames.CONFIG)
    if not daemon_running(conf.address, conf.port):
        # need to remove the command from the program name
        args[0] = args[0].replace(" start", "")
        start_daemon(args)

def dostop(args):
    if len(args) == 2 and args[1] == "--help":
        stdout.write("Stop the background neubot instance.\n")
        stdout.write("Usage: %s\n" % args[0])
        exit(0)
    if len(args) > 1:
        stderr.write("Usage: %s\n" % args[0])
        exit(1)
    conf = ui.UIConfig()
    conf.read(pathnames.CONFIG)
    if daemon_running(conf.address, conf.port):
        stop_daemon(conf.address, conf.port)

TABLE = {
    "database"   : database.main,
    "help"       : dohelp,
    "http"       : http.main,
    "httpd"      : httpd.main,
    "rendezvous" : rendezvous.main,
    "speedtest"  : speedtest.main,
    "start"      : dostart,
    "stop"       : dostop,
    "ui"         : ui.main,
}

#
# Gtk bindings might not be installed and we don't want
# to prevent the user running neubot in this case, but
# just to warn she that some graphical features are not
# available.
#

def cannot_import_gtk(args):
    command = args[0].split()[-1]
    log.error("%s: fatal: Can't import Gtk bindings for Python." % command)
    exit(1)

try:
    import gtk
except ImportError:
    TABLE["statusicon"] = cannot_import_gtk
else:
    from neubot import statusicon
    TABLE["statusicon"] = statusicon.main

DEFAULT = "rendezvous"

#
# Without arguments try to guess "the right thing to do"
# depending on the operating system and on the available
# environment.
#

def main(args):
    pathnames.checkdirs()
    if len(args) == 1:
        conf = ui.UIConfig()
        conf.read(pathnames.CONFIG)
        if not daemon_running(conf.address, conf.port):
            start_daemon(args)
        uri = "http://%s:%s/" % (conf.address, conf.port)
        if os.name != "posix" or os.environ.has_key("DISPLAY"):
            webbrowser.open(uri)
    else:
        _main_with_args(args)

#
# Make sure that _do_main() always receives
# the program name as the first argument and
# a command (not an option) as the second
# argument.
#

def _main_with_args(args):
    command = args[1]
    if command.startswith("-"):
        args.insert(1, DEFAULT)
        _do_main(args, added_command=True)
        return
    if command.startswith("http://"):
        args.insert(1, DEFAULT)
        _do_main(args, added_command=True)
        return
    _do_main(args)

#
# Lookup the main function for the specified
# command or print an error message.
#

def _do_main(args, added_command=False):
    command = args[1]
    try:
        func = TABLE[command]
    except KeyError:
        stderr.write("The '%s' command does not exist\n" % command)
        dohelp(args, stderr)
        exit(1)
    _do_fixup_and_invoke(func, args, added_command)

#
# Make sure that args[] mirrors what the user typed:
# remove the command name if we added it, or collapse
# the program name and the command into the first arg
# for the invoked main to treat it as the program
# name.
#

def _do_fixup_and_invoke(func, args, added_command):
    if not added_command:
        copy, args = args, []
        args.append(copy[0] + " " + copy[1])
        for arg in copy[2:]:
            args.append(arg)
    else:
        del args[1]
    _do_invoke(func, args)

#
# And finally invoke main()...
#

def _do_invoke(func, args):
    try:
        if os.environ.has_key("NEUBOT_TRACE"):
            setprofile(debug.trace)
        func(args)
    except SystemExit, e:
        code = int(str(e))
        exit(code)
    except:
        log.exception()
        exit(1)

#
# Daemon functions
# Here there is code to guess whether an instance of neubot
# is already running and code to start a background instance
# if needed.
#

import webbrowser
import subprocess
import httplib
import socket

def daemon_running(address, port):
    isrunning = False
    try:
        connection = httplib.HTTPConnection(address, port)
        connection.request("GET", "/api/version")
        response = connection.getresponse()
        if response.status == 200:
            isrunning = True
        connection.close()
    except (httplib.HTTPException, socket.error):
        pass
    return isrunning

def start_daemon(args):
    args[0] = os.path.abspath(args[0])
    args.append("rendezvous")
    #
    # With UNIX we use call() because we know that
    # the called instance of neubot is going to fork
    # in background.
    #
    if os.name != "posix":
        call = subprocess.Popen
    else:
        call = subprocess.call
    try:
        call(args)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        log.error("Can't exec: %s" % str(args))
        log.exception()
        exit(1)

def stop_daemon(address, port):
    try:
        connection = httplib.HTTPConnection(address, port)
        connection.request("POST", "/api/exit")
        response = connection.getresponse()
        connection.close()
    except (httplib.HTTPException, socket.error):
        pass

if __name__ == "__main__":
    main(argv)
