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

from neubot.net.pollers import dispatch
from neubot.http.api import compose
from neubot.http.api import send, recv

TIMEOUT = 250
STATECHANGE = "http://127.0.0.1:9774/state/change"
STATE = "http://127.0.0.1:9774/state"

class TrayIcon:

    #
    # For now we just use one of the stock icons to notify the
    # user that we are performing network activity.
    # TODO We need to fill the code that generates the popup menu
    # and we need to decide what to do when we are activated.
    #

    def __init__(self):
        self.needsend = True
        self.havestate = False
        self.tray = gtk.StatusIcon()
        self.tray.set_from_icon_name(gtk.STOCK_NETWORK)                 # XXX
        self.tray.connect("popup-menu", self.on_popup_menu)
        self.tray.connect("activate", self.on_activate)
        self.tray.set_visible(False)
        self.update()

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

    def update(self):
        if self.needsend:
            uri = STATE
            if self.havestate:
                uri = STATECHANGE
            m = compose(method="GET", uri=uri, keepalive=False)
            send(m, sent=self.sent, cantsend=self.cantsend)
        dispatch()
        gobject.timeout_add(TIMEOUT, self.update)

    #
    # We need to be careful and we must hide the icon in case
    # of errors.
    # When we receive the response we read the whole body at
    # once, and this is not so safe--we should check that it
    # its not too big, instead.
    #

    def cantsend(self, m):
        self.needsend = True
        self.tray.set_visible(False)
        self.havestate = False

    def sent(self, m):
        recv(m, received=self.received, cantrecv=self.cantrecv)

    def received(self, m):
        if m.code == "200":
            body = m.body.read().strip()                                # XXX
            if not self.havestate:
                self.havestate = True
            if body != "SLEEPING":
                self.tray.set_visible(True)
                #self.tray.set_blinking(True)
                self.tray.set_tooltip("neubot: " + body.lower())
            else:
                self.tray.set_visible(False)
        self.needsend = True

    def cantrecv(self, m):
        self.needsend = True
        self.tray.set_visible(False)
        self.havestate = False

if __name__ == "__main__":
    gtk.gdk.threads_init()
    app = TrayIcon()
    gtk.main()
