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

import re

def infobox(message):
    window = gtk.Window()
    window.set_title("Neubot 0.3.7")
    window.connect("delete_event", lambda p1, p2: gtk.main_quit())
    window.connect("destroy", lambda w: gtk.main_quit())

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

    button = gtk.Button(label="Close", stock=gtk.STOCK_CLOSE)
    button.connect("clicked", lambda w: gtk.main_quit())
    vbox.pack_start(button)

    window.add(vbox)
    window.show_all()
    gtk.main()

if __name__ == "__main__":
    infobox("An updated version of Neubot is available "
                 "at <http://www.neubot.org/download>")
