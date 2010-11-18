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

from neubot import log
from threading import Thread
from neubot.utils import become_daemon
from neubot.ui import SimpleStateTracker
from getopt import GetoptError
from getopt import getopt
from sys import stdout
from sys import stderr
from sys import argv
from time import sleep
from sys import exit

import webbrowser
#import gobject
import signal
import gtk

# default address and port
ADDRESS = "127.0.0.1"
PORT = "9774"
VERSION = "0.3.1"

class StateTrackerAdapter(SimpleStateTracker):
    def __init__(self, icon, address, port):
        SimpleStateTracker.__init__(self, address, port)
        self.state = None
        self.icon = icon
        self.update = ()

    def clear(self):
        self.icon.update_state(None, None)
        self.update = ()

    def set_update(self, ver, uri):
        self.update = (ver, uri)

    def set_active(self, active):
        if active.lower() != "true":
            self.state = "SLEEPING"

    def set_current_activity(self, activity):
        self.state = activity.upper()

#   def set_extra(self, name, value):
#       pass

    def write(self):
        self.icon.update_state(self.state, self.update)

class StateTrackerThread(Thread):
    def __init__(self, icon, address, port):
        Thread.__init__(self)
        self.adapter = StateTrackerAdapter(icon, address, port)
        self.interrupt = self.adapter.interrupt

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
        self.adapter.loop()

#
# The icon in the notification area employs Gtk because I was not
# able to find a way to implement it using Tk (if there is a clean
# way to do that, please let me know).  So, I decided to use Gtk
# because it is installed by default under Ubuntu, which is one of
# the most common GNU/Linux distros.
#

# TODO move in pathnames when we install icon for all Unices
ICON = "/usr/share/icons/hicolor/scalable/apps/neubot.svg"
import os.path

class StatusIcon:

    #
    # We use the stock icon that represents network activity but
    # it would be better to design and ship an icon for Neubot.
    #

    def __init__(self, address, port, blink, nohide):
        self.address = address
        self.port = port
        self.menu = False
        self.blink = blink
        self.nohide = nohide
        self.icon = gtk.StatusIcon()
        # The icon might not exist (e.g. running from sources)
        self.icon.set_from_icon_name(gtk.STOCK_NETWORK)
        if os.path.exists(ICON):
            self.icon.set_from_file(ICON)
        self.icon.connect("popup-menu", self.on_popup_menu)
        self.icon.connect("activate", self.on_activate)
        self.icon.set_visible(self.nohide)
        self.update_item = None

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
        webbrowser.open(uri, new=2, autoraise=True)

    def _do_quit(self, *args):
        gtk.main_quit()

    def on_activate(self, *args):
        self._do_open_browser()

    #
    # Here we need to surround the code with threads_enter() and
    # threads_leave() because this function is called from another
    # thread context.
    # See: http://bit.ly/hp8Ot [operationaldynamics.com]
    #

    def update_state(self, state, update):
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
        if update:
            if not self.update_item:
                ver, uri = update
                item = gtk.MenuItem(label="Update to %s" % ver)
                item.connect("activate", self._do_download_update, uri)
                self.menu.add(item)
                self.menu.show_all()
                self.update_item = item
        else:
            if self.update_item:
                self.menu.remove(self.update_item)
                self.update_item = None
        gtk.gdk.threads_leave()

    def _do_download_update(self, *args):
        webbrowser.open(args[1], new=2, autoraise=True)

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

USAGE = "Usage: %s [-BdnVv] [--help] [[address] port]\n"

HELP = USAGE +								\
"Options:\n"								\
"  -B     : Blink the icon when performing a test.\n"			\
"  -d     : Debug mode, don't detach from shell.\n"			\
"  --help : Print this help screen and exit.\n"				\
"  -n     : Do not hide the icon when neubot is idle.\n"		\
"  -V     : Print version number and exit.\n"				\
"  -v     : Run the program in verbose mode.\n"

def main(args):
    daemonize = True
    blink = False
    nohide = False
    # parse
    try:
        options, arguments = getopt(args[1:], "BdnVv", ["help"])
    except GetoptError:
        stderr.write(USAGE % args[0])
        exit(1)
    for name, value in options:
        if name == "-B":
            blink = True
        elif name == "-d":
            daemonize = False
        elif name == "--help":
            stdout.write(HELP % args[0])
            exit(0)
        elif name == "-n":
            nohide = True
        elif name == "-V":
            stderr.write(VERSION + "\n")
            exit(0)
        else:
            log.verbose()
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
    if daemonize:
        become_daemon()
    # run
    gtk.gdk.threads_init()
    icon = StatusIcon(address, port, blink, nohide)
    tracker = StateTrackerThread(icon, address, port)
    tracker.daemon = True
    tracker.start()
    # See: http://bit.ly/hp8Ot [operationaldynamics.com]
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()
    tracker.interrupt()

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
