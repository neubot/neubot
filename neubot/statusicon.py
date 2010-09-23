# neubot/statusicon.py
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

# Portions of this file are a derivative work of portions of:
#Facebook Notify - Facebook status notifier for GNOME
#Copyright (C) 2009 John Stowers <john.stowers@gmail.com>
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
# Status icon for notification area
# BTW we might also consider using alternate mechanisms
# because in certain environments notification area is
# being deprecated, e.g.:
#
#     http://bit.ly/dxI7vi [design.canonical.com]
#

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from threading import Thread
from httplib import HTTPConnection
from httplib import HTTPException
from getopt import GetoptError
from getopt import getopt
from os import isatty
from sys import stdout
from sys import stderr
from sys import argv
from time import sleep
from sys import exit

import traceback
import webbrowser
import socket
#import gobject
import signal
import gtk

# default address and port
ADDRESS = "127.0.0.1"
PORT = "9774"
VERSION = "0.2.5"

#
# Track neubot(1) state using GET once to get the state value and
# then using long-polling to update the value when it changes.
# We don't want to meld StateTracker and StateTrackerThread because
# it might be useful to run StateTracker from the main thread, for
# example for testing purpose.  BTW, this is also the reason why
# the reference to the status-icon is optional (it's not possible
# to run this class in the same thread of the status-icon).
# We don't use neubot.http(3) here for various reasons, including
# problems integrating it with Gtk's main loop, and pygtk being
# compiled for Python 2.5 on my OS (while neubot, at the moment of
# writing is Python 2.6+).
#

class StateTracker:
    def __init__(self, address, port, icon=None, verbose=False):
        self.address = address
        self.port = port
        self.icon = icon
        self.verbose = verbose
        self.state = None

    def update_state(self):
        error = False
        connection = None
        try:
            connection = HTTPConnection(self.address, self.port)
            if self.verbose:
                connection.set_debuglevel(1)
            uri = "/state"
            # XXX using obsolete '/change' suffix (better to use '/comet')
            if self.state:
                uri += "/change"
            connection.request("GET", uri)
            response = connection.getresponse()
            if response.status == 200:
                self.state = response.read().strip()
                if self.icon:
                    self.icon.update_state(self.state)
                else:
                    stdout.write("%s\n" % self.state)
            else:
                error = True
                if isatty(stderr.fileno()):
                    stderr.write("Response: %s\n" % response.status)
        except (HTTPException, socket.error):
            error = True
            if isatty(stderr.fileno()):
                traceback.print_exc()
        if error:
            self.state = None
            # to blank the tooltip
            if self.icon:
                self.icon.update_state(self.state)
        return error

class StateTrackerThread(Thread):
    def __init__(self, address, port, icon=None, verbose=False):
        Thread.__init__(self)
        self.statetracker = StateTracker(address, port, icon, verbose)
        self.stop = False

    #
    # Here we ASSUME that we are running a *detached* thread
    # of execution--in other words the main program is going
    # to exit even if this thread is still running--and for
    # this reason we feel free to invoke sleep().
    # The sleep(3) is here because I am Gtk-ignorant and I
    # want to be sure that we don't update_state() before we
    # enter into gtk.main(), since I don't know whether it
    # is harmless or not.
    # When there is an error in updating the state we sleep
    # for a while to avoid consuming too much CPU (think for
    # example at the case when neubot(1) is not running and
    # in each iteration the connection is refused).
    #

    def run(self):
        sleep(3)
        while not self.stop:                                            # XXX
            error = self.statetracker.update_state()
            if error:
                sleep(5)

#
# The icon in the notification area employs Gtk because I was not
# able to find a way to implement it using Tk (if there is a clean
# way to do that, please let me know).  So, I decided to use Gtk
# because it is installed by default under Ubuntu, which is one of
# the most common GNU/Linux distros.
#

class StatusIcon:

    #
    # We use the stock icon that represents network activity but
    # it would be better to design and ship an icon for Neubot.
    # TODO We need to fill the code that generates the popup menu
    # and we need to decide what to do when we are activated.
    #

    def __init__(self, address, port, blink, nohide):
        self.address = address
        self.port = port
        self.menu = False
        self.blink = blink
        self.nohide = nohide
        self.icon = gtk.StatusIcon()
        self.icon.set_from_icon_name(gtk.STOCK_NETWORK)                 # XXX
        self.icon.connect("popup-menu", self.on_popup_menu)
        self.icon.connect("activate", self.on_activate)
        if not self.nohide:
            self.icon.set_visible(False)

    def on_popup_menu(self, status, button, time):
        if not self.menu:
            self.menu = gtk.Menu()
            # open neubot
            item = gtk.MenuItem(label="Open neubot")
            item.connect("activate", self._do_open_browser)
            self.menu.add(item)
            # quit
            item = gtk.MenuItem(label="Quit")
            item.connect("activate", self._do_quit)
            self.menu.add(item)
            # done
            self.menu.show_all()
        self.menu.popup(None, None, gtk.status_icon_position_menu,
                        button, time, self.icon)

    def _do_open_browser(self, *args):
        uri = "http://%s:%s/" % (self.address, self.port)
        # XXX This call might be blocking with certain browsers
        webbrowser.open(uri, new=2)

    def _do_quit(self, *args):
        gtk.main_quit()

    def on_activate(self, *args):
        pass

    #
    # Here we need to surround the code with threads_enter() and
    # threads_leave() because this function is called from another
    # thread context.
    # See: http://bit.ly/hp8Ot [operationaldynamics.com]
    #

    def update_state(self, state):
        gtk.gdk.threads_enter()
        if state:
            self.icon.set_tooltip("Neubot: " + state)
            if state not in [ "SLEEPING", "UNKNOWN" ]:
                if self.blink:
                    self.icon.set_blinking(True)
                if not self.nohide:
                    self.icon.set_visible(True)
            else:
                if not self.nohide:
                    self.icon.set_visible(False)
                if self.blink:
                    self.icon.set_blinking(False)
        else:
            self.icon.set_tooltip("Neubot: ???")
            if not self.nohide:
                self.icon.set_visible(False)
            if self.blink:
                self.icon.set_blinking(False)
        gtk.gdk.threads_leave()

#
# Main program
# By default the icon is not visible because IIUC the
# notification area should be used for transient state
# notification only--and so the icon is visible only when
# neubot is performing some transmission test.
# Of course, YMMV and so there are: a switch to keep the
# icon always visible; and a switch to blink the icon when
# neubot is performing some transmission test.
#

USAGE = "Usage: %s [-BnVv] [--help] [[address] port]\n"

HELP = USAGE +								\
"Options:\n"								\
"  -B     : Blink the icon when performing a test.\n"			\
"  --help : Print this help screen and exit.\n"				\
"  -n     : Do not hide the icon when neubot is idle.\n"		\
"  -V     : Print version number and exit.\n"				\
"  -v     : Run the program in verbose mode.\n"

def main(args):
    verbose = False
    blink = False
    nohide = False
    # parse
    try:
        options, arguments = getopt(args[1:], "BnVv", ["help"])
    except GetoptError:
        stderr.write(USAGE % args[0])
        exit(1)
    for name, value in options:
        if name == "-B":
            blink = True
        elif name == "--help":
            stdout.write(HELP % args[0])
            exit(0)
        elif name == "-n":
            nohide = True
        elif name == "-V":
            stderr.write(VERSION + "\n")
            exit(0)
        else:
            verbose = True
    # arguments
    if len(arguments) >= 3:
        stderr.write(USAGE % args[0])
        exit(1)
    elif len(arguments) == 2:
        address = arguments[0]
        port = arguments[1]
    elif len(arguments) == 1:
        address = ADDRESS
        port = arguments[0]
    else:
        address = ADDRESS
        port = PORT
    # run
    gtk.gdk.threads_init()
    icon = StatusIcon(address, port, blink, nohide)
    tracker = StateTrackerThread(address, port, icon, verbose)
    tracker.daemon = True
    tracker.start()
    # See: http://bit.ly/hp8Ot [operationaldynamics.com]
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()
    tracker.stop = True

#
# When we are invoked directly we need to set-up a custom
# signal handler because we want Ctrl-C to break Gtk's main
# loop (see http://bit.ly/c2mbSl [faq.pygtk.org]).
# OTOH when neubot(1) invokes the main() function we don't
# need to do that because neubot(1) already installs its
# custom signal handler for SIGINT.
#

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main(argv)
