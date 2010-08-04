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

import sys

if __name__ == "__main__":
    sys.path.append(".")

import gtk
import gobject

import neubot

TIMEOUT = 250
STATECHANGE = "http://127.0.0.1:9774/state/change"
STATE = "http://127.0.0.1:9774/state"

class TrayIcon:
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

    def update(self):
        if self.needsend:
            uri = STATE
            if self.havestate:
                uri = STATECHANGE
            m = neubot.http.compose(method="GET", uri=uri, keepalive=False)
            neubot.http.send(m, sent=self.sent, cantsend=self.cantsend)
        neubot.net.dispatch()
        gobject.timeout_add(TIMEOUT, self.update)

    def cantsend(self, m):
        self.needsend = True
        self.tray.set_visible(False)
        self.havestate = False

    def sent(self, m):
        neubot.http.recv(m, received=self.received, cantrecv=self.cantrecv)

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
