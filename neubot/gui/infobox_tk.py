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

def _on_click(event):
    txt = event.widget["text"]
    match = re.match("<(.*)>", txt)
    link = match.group(1)
    webbrowser.open(link)

def _on_enter(event):
    widget = event.widget
    widget.config(cursor="hand2")

def _on_leave(event):
    widget = event.widget
    widget.config(cursor="")

def infobox(message):
    root = Tkinter.Tk()
    root.title("Neubot 0.3.7")

    for txt in re.split("(<[A-Za-z0-9:/_#.]+>)", message):
        if txt and txt[0] == "<":
            label = Tkinter.Label(text=txt, foreground="blue")
            label.bind("<Button-1>", _on_click)
            label.bind("<Enter>", _on_enter)
            label.bind("<Leave>", _on_leave)
            label.pack()
        elif txt:
            label = Tkinter.Label(text=txt)
            label.pack()

    button = Tkinter.Button(root, text="Close", command=root.quit)
    button.pack()

    root.focus_set()
    root.mainloop()

if __name__ == "__main__":
    infobox("An updated version of Neubot is available "
                 "at <http://www.neubot.org/download>")
