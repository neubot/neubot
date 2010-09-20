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
from neubot import log
from sys import argv
from os import environ

# cheating a bit
from neubot.http import clients as http
from neubot.http import servers as httpd

from neubot import database
from neubot import rendezvous
from neubot import speedtest
from neubot import ui

TABLE = {
    "database"   : database.main,
    "http"       : http.main,
    "httpd"      : httpd.main,
    "rendezvous" : rendezvous.main,
    "speedtest"  : speedtest.main,
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
# Make sure that _do_main() always receives
# the program name as the first argument and
# a command (not an option) as the second
# argument.
#

def main(args):
    if len(args) == 1:
        args.append(DEFAULT)
        _do_main(args, added_command=True)
        return
    command = args[1]
    if command.startswith("-"):
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
        log.error("The '%s' command does not exist." % command)
        log.info("Here's a list of available commands:")
        for key in sorted(TABLE.keys()):
            log.info("  %s" % key)
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
        if environ.has_key("NEUBOT_TRACE"):
            setprofile(debug.trace)
        func(args)
    except SystemExit, e:
        code = int(str(e))
        exit(code)
    except:
        log.exception()
        exit(1)

if __name__ == "__main__":
    main(argv)
