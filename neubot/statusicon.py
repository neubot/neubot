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
#

from sys import path
if __name__ == "__main__":
    path.insert(0, ".")

import gtk
import gobject

from neubot.http.clients import SimpleClient
from neubot.http.messages import Message
from neubot.http.messages import compose
from neubot.net.pollers import dispatch
from neubot.net.pollers import sched

# milliseconds between each dispatch() call
TIMEOUT = 250

#
# Track the value of state, using GET /state the first time and
# then GET /state/change later (in the latter case the UI server
# employs comet and so we are notified only when the state changes
# or a certain timeout expires).
# If we cannot connect or the connection is lost for some reason,
# we try again five seconds in the future (just to avoid wasting
# tons of resources when Neubot is down for some reason).
#

class StateTracker(SimpleClient):
    def __init__(self):
        self.state = None
        self._update()

    def _update(self):
        m = Message()
        compose(m, method="GET", uri="http://127.0.0.1:9774/state")
        self.send(m)

    def connect_error(self):
        self.state = None
        sched(5, self._update)

    def sendrecv_error(self):
        self.state = None
        sched(5, self._update)

    def got_response(self, request, response):
        if response.code == "200":
            self.state = response.body.read().strip()
            m = Message()
            compose(m, method="GET", uri="http://127.0.0.1:9774/state/change")
            self.send(m)
        else:
            self.state = None

#
# The icon in the notification area.
# We can't use Tk here because it seems that there is not notification
# are support into it.
# So we employ Gtk because it's installed in Ubuntu which is one of
# the systems we want to provide an user friendly interface for.
#

class TrayIcon:

    #
    # For now we just use one of the stock icons to notify the
    # user that we are performing network activity.
    # TODO We need to fill the code that generates the popup menu
    # and we need to decide what to do when we are activated.
    #

    def __init__(self):
        self.tracker = StateTracker()
        self.tray = gtk.StatusIcon()
        self.tray.set_from_icon_name(gtk.STOCK_NETWORK)                 # XXX
        self.tray.connect("popup-menu", self.on_popup_menu)
        self.tray.connect("activate", self.on_activate)
        self.tray.set_visible(False)
        self._update()

    def on_popup_menu(self, status, button, time):
        pass

    def on_activate(self, *args):
        pass

    #
    # The base principle to nest our loop and Gtk's one is that
    # we are periodically invoked by Gtk.  This is not efficient
    # but should be enough because (as I understand it) the main
    # purpose of the status icon is the one of providing users
    # a way to stop a running test--then it's Ok to update every
    # 1/4 of second.  [And probably we should pop the icon out
    # only if the test lasts for more than one second, because a
    # test that lasts less than one second should not be a problem
    # for most users.]
    #

    def _update(self):
        dispatch()
        gobject.timeout_add(TIMEOUT, self._update)
        if self.tracker.state and self.tracker.state != "SLEEPING":
            self.tray.set_tooltip("Neubot: " + self.tracker.state)
#           self.tray.set_blinking(True)
            self.tray.set_visible(True)
        else:
            self.tray.set_visible(False)

if __name__ == "__main__":
    gtk.gdk.threads_init()
    app = TrayIcon()
    gtk.main()
