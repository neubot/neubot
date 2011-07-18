# neubot/statusicon.py

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
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
# ===========================================================
# Portions of this file are a derivative work of portions of:
# ===========================================================
#
# Facebook Notify - Facebook status notifier for GNOME
# Copyright (C) 2009 John Stowers <john.stowers@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#
# Status icon for notification area
# BTW we might also consider using alternate mechanisms
# because in certain environments notification area is
# being deprecated, e.g.:
#
#     http://bit.ly/dxI7vi [design.canonical.com]
#

import sys
import os.path
import webbrowser
import threading
#import gobject
import signal
import gtk
import getopt
import time

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot import system
from neubot.api.client import APIStateTracker
from neubot.net.poller import POLLER
from neubot.log import LOG

# default address and port
ADDRESS = "127.0.0.1"
PORT = "9774"

VERSION = "0.4-rc3"

class StateTrackerAdapter(APIStateTracker):

    def process_dictionary(self, dictionary):
        update = ()

        if "events" in dictionary and "update" in dictionary["events"]:
            udict = dictionary["events"]["update"]
            if "version" in udict and "uri" in udict:
                update = udict["version"], udict["uri"]

        state = dictionary["current"]

        icon = self.conf.get("statusicon.icon", None)
        if icon:
            icon.update_state(state, update)

    def notify_error(self, message):
        icon = self.conf.get("statusicon.icon", None)
        if icon:
            icon.update_state(None, None)

class StateTrackerThread(threading.Thread):
    def __init__(self, icon, address, port):
        threading.Thread.__init__(self)
        self.adapter = StateTrackerAdapter(POLLER)
        self.adapter.configure({
            "statusicon.icon": icon,
            "api.client.address": address,
            "api.client.port": port,
        })
        # XXX
        self.interrupt = self.adapter.interrupt

    #
    # Here we ASSUME that we are running a *detached* thread
    # of execution -- in other words the main program is going
    # to exit even if this thread is still running -- and for
    # this reason we feel free to invoke sleep().
    # The sleep() is there because I am Gtk-ignorant and I
    # want to be sure that we don't update_state() before we
    # enter into gtk.main(), since I don't know whether it
    # is harmless or not.
    # When there is an error in updating the state we sleep
    # for a while to avoid consuming too much CPU (think for
    # example at the case when neubot() is not running and
    # in each iteration the connection is refused).
    #

    def run(self):
        time.sleep(3)
        self.adapter.loop()

#
# The icon in the notification area employs Gtk because I was not
# able to find a way to implement it using Tk (if there is a clean
# way to do that, please let me know).  So, I decided to use Gtk
# because it is installed by default under Ubuntu, which is one of
# the most common GNU/Linux distros.
#

ICON = "@PREFIX@/share/icons/hicolor/scalable/apps/neubot.svg"
if ICON.startswith("@"):
    ICON = "icons/neubot.svg"

class StatusIcon(object):

    def __init__(self, address, port, blink, nohide):
        self.address = address
        self.port = port
        self.blink = blink
        self.nohide = nohide

        self.icon = gtk.StatusIcon()
        self.icon.set_from_icon_name(gtk.STOCK_NETWORK)
        if os.path.exists(ICON):
            self.icon.set_from_file(ICON)

        self.icon.connect("popup-menu", self.on_popup_menu)
        self.icon.connect("activate", self.on_activate)
        self.icon.set_visible(self.nohide)
        self.update_item = None

        self.menu = gtk.Menu()

        item = gtk.MenuItem(label="Open Web Interface")
        item.connect("activate", self._do_open_browser)
        self.menu.add(item)

        item = gtk.MenuItem(label="Close Status Icon")
        item.connect("activate", self._do_quit)
        self.menu.add(item)

        self.menu.show_all()

    def on_popup_menu(self, status, button, time):
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
            self.icon.set_tooltip("Neubot daemon state: " + state)
            if state != "idle":
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
            self.icon.set_tooltip("Neubot daemon state: unknown")
            if not self.nohide:
                self.icon.set_visible(False)
            if self.blink:
                self.icon.set_blinking(False)

        if update:
            if not self.update_item:
                ver, uri = update
                item = gtk.MenuItem(label="Update neubot to %s" % ver)
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
# The icon is always visible in the notification area,
# and we know that this is not what the notification area
# is designed for in the first place.  But we need to
# provide a simple and visual feedback that neubot daemon
# is running.  If you prefer an even more aggressive
# icon behavior, there is a switch that blinks the icon
# while neubot is running a transmission test.  And if
# you prefer the default "notification" semantic of the
# area, there is a switch to silence the icon unless the
# daemon is performing a transmission test.
#

USAGE = "Usage: %s [-BdnqVv] [--help] [[address] port]\n"

HELP = USAGE +								\
"Options:\n"								\
"  -B     : Blink the icon when performing a test.\n"			\
"  -d     : Debug mode, don't detach from shell.\n"			\
"  --help : Print this help screen and exit.\n"				\
"  -n     : Do not hide the icon when neubot is idle (default)\n"	\
"  -q     : Hide the icon when neubot is idle.\n"			\
"  -V     : Print version number and exit.\n"				\
"  -v     : Run the program in verbose mode.\n"

def main(args):

    daemonize = True
    blink = False
    nohide = True

    try:
        options, arguments = getopt.getopt(args[1:], "BdnqVv", ["help"])
    except getopt.GetoptError:
        sys.stderr.write(USAGE % args[0])
        sys.exit(1)

    for name, value in options:
        if name == "-B":
            blink = True
        elif name == "-d":
            daemonize = False
        elif name == "--help":
            sys.stdout.write(HELP % args[0])
            sys.exit(0)
        elif name == "-n":
            nohide = True
        elif name == "-q":
            nohide = False
        elif name == "-V":
            sys.stderr.write(VERSION + "\n")
            sys.exit(0)
        elif name == "-v":
            LOG.verbose()

    if len(arguments) >= 3:
        sys.stderr.write(USAGE % args[0])
        sys.exit(1)
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
        system.change_dir()
        system.go_background()
        LOG.redirect()
    system.drop_privileges(LOG.error)

    gtk.gdk.threads_init()
    icon = StatusIcon(address, port, blink, nohide)
    tracker = StateTrackerThread(icon, address, port)
    tracker.daemon = True
    tracker.start()

    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()
    tracker.interrupt()

#
# When we are invoked directly we need to set-up a custom
# signal handler because we want Ctrl-C to break Gtk's main
# loop (see http://bit.ly/c2mbSl [faq.pygtk.org]).
# OTOH when neubot() invokes the main() function we don't
# need to do that because neubot() already installs its
# custom signal handler for SIGINT.
#

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main(sys.argv)
