# neubot/speedtest/compat.py

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
# Eventually one day these messages will go away and we
# will use dictionaries serialized and deserialized using
# JSON.  Dream off.  This bits of code will stay there
# quite some time but I put them into a file named compat.py
# to signal that these are constraints coming from the
# past.
#

class SpeedtestCollect(object):
    def __init__(self):
        self.client = ""
        self.timestamp = 0
        self.internalAddress = ""
        self.realAddress = ""
        self.remoteAddress = ""
        self.connectTime = 0.0
        self.latency = 0.0
        self.downloadSpeed = 0.0
        self.uploadSpeed = 0.0
        self.privacy_informed = 0
        self.privacy_can_collect = 0
        self.privacy_can_share = 0

class SpeedtestNegotiate_Response(object):
    def __init__(self):
        self.authorization = ""
        self.publicAddress = ""
        self.unchoked = 0
        self.queuePos = 0
        self.queueLen = 0
