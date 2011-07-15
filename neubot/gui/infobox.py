# neubot/gui/infobox.py

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
# and hyperlinks using the available toolkit.
#

InfoBox = None

if not InfoBox:
    try:
        from neubot.gui.infobox_gtk import InfoBox
    except ImportError:
        pass

# Disabled!
#if not infobox:
#    try:
#        from neubot.gui.infobox_win32 import InfoBox
#    except ImportError:
#        pass

if not InfoBox:
    try:
        from neubot.gui.infobox_tk import InfoBox
    except ImportError:
        pass

if not InfoBox:
    InfoBox = lambda message: None
