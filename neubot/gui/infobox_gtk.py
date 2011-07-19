# neubot/gui/infobox_gtk.py

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
# Display a simple window with informative messages
# and hyperlinks using PyGtk.
#

import pygtk
pygtk.require("2.0")
import gtk

import gobject
import os.path
import re

ICON = "@PREFIX@/share/icons/hicolor/scalable/apps/neubot.svg"
if ICON.startswith("@"):
    ICON = "icons/neubot.svg"
if not os.path.isfile(ICON):
    ICON = gtk.STOCK_NETWORK

class _InfoBox(object):

    def _cleanup(self, *args):
        self._window.destroy()
        gtk.main_quit()

    def _update_timeo(self):
        self.timeo = self.timeo -1
        if self.timeo == 0:
            self._cleanup()
            return gtk.FALSE
        self._button.set_label("Close (%d sec)" % self.timeo)
        return gtk.TRUE

    def __init__(self, message, timeo=30):
        self._window = gtk.Window()
        self._window.set_title("Neubot 0.4-rc4")
        self._window.set_icon_from_file(ICON)

        self._window.connect("delete_event", self._cleanup)
        self._window.connect("destroy", self._cleanup)

        vbox = gtk.VBox()

        for txt in re.split("(<.+?>)", message):
            if txt and txt[0] == "<":
                label = gtk.Label()

                link = txt[1:-1]
                markup = '<a href="%s">%s</a>' % (link, link)
                label.set_markup(markup)

                vbox.pack_start(label)
            elif txt:
                label = gtk.Label(txt)
                vbox.pack_start(label)

        self.timeo = timeo

        table = gtk.Table(1, 3, True)
        vbox.pack_start(table)

        self._button = gtk.Button(stock=gtk.STOCK_CLOSE)
        self._button.set_label("Close (%d sec)" % self.timeo)
        self._button.connect("clicked", self._cleanup)
        table.attach(self._button, 1, 2, 0, 1)

        gobject.timeout_add(1000, self._update_timeo)

        self._window.add(vbox)
        self._window.show_all()
        gtk.main()

if __name__ == "__main__":
    _InfoBox("An updated version of Neubot is available "
             "at <http://www.neubot.org/download>")
