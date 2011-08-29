# neubot/gui/infobox_tk.py

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
# and hyperlinks using Tkinter.
#

import Tkinter
import webbrowser
import re

#
# XXX Here I would like to import an icon for the window
# but I have not found an easy way to do that using a PNG
# or SVG image.  Does anyone knows the trick?
#
class _InfoBox(object):

    def _on_click(self, event):
        txt = event.widget["text"]
        webbrowser.open(txt)

    def _on_enter(self, event):
        widget = event.widget
        widget.config(cursor="hand2")

    def _on_leave(self, event):
        widget = event.widget
        widget.config(cursor="")

    def _dtor(self, *args):
        self._root.destroy()

    def _update_timeo(self):
        self._timeo = self._timeo -1
        if self._timeo == 0:
            self._dtor()
            return
        self._button.config(text="Close (%d sec)" % self._timeo)
        self._root.after(1000, self._update_timeo)

    def __init__(self, message, timeo=30):
        self._root = Tkinter.Tk()
        self._root.title("Neubot 0.4.1-rc4")
        self._root.protocol("WM_DELETE_WINDOW", self._dtor)

        for txt in re.split("(<.+?>)", message):
            if txt and txt[0] == "<":
                link = txt[1:-1]
                label = Tkinter.Label(text=link, foreground="blue")
                label.bind("<Button-1>", self._on_click)
                label.bind("<Enter>", self._on_enter)
                label.bind("<Leave>", self._on_leave)
                label.pack()
            elif txt:
                label = Tkinter.Label(text=txt)
                label.pack()

        self._timeo = timeo

        self._button = Tkinter.Button(self._root, command=self._dtor)
        self._button.config(text="Close (%d sec)" % self._timeo)
        self._button.pack()

        self._root.after(1000, self._update_timeo)

        self._root.focus_set()
        self._root.mainloop()

if __name__ == "__main__":
    _InfoBox("An updated version of Neubot is available "
             "at <http://www.neubot.org/download>")
