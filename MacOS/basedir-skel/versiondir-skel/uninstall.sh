#!/bin/sh

#
# Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>,
#  Universita` degli Studi di Milano
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

# Stop neubot daemon
launchctl stop org.neubot
launchctl unload /Library/LaunchDaemons/org.neubot.plist

# Commented-out because it's meaningful for logged users only
#launchctl stop org.neubot.notifier
#launchctl unload /Library/LaunchAgents/org.neubot.notifier.plist

# Installer
rm -rf /usr/local/share/neubot
rm -f /Library/LaunchDaemons/org.neubot.plist
rm -f /Library/LaunchAgents/org.neubot.notifier.plist

#
# VERSIONDIR/start.sh
# Please note that we `rmdir` various directories because we
# want them removed iff they are empty!
#
rm -f /Applications/Neubot.app
rm -f /usr/local/bin/neubot
rmdir /usr/local/bin
rm -f /usr/local/share/man/man1/neubot.1
rmdir /usr/local/share/man/man1
rmdir /usr/local/share/man
dscl . -delete /Users/_neubot
dscl . -delete /Groups/_neubot
dscl . -delete /Users/_neubot_update
dscl . -delete /Groups/_neubot_update

# Neubot itself
rm -rf /var/neubot/					# database dir

# Tell the system Neubot is no more
rm -rf /Library/Receipts/Neubot-*.pkg/
rm -rf /var/db/receipts/org.neubot.*

# Won't hurt
sync
