# testing/source.py
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

import neubot

class Source:
    def __init__(self, stream):
        self.buffer = "A" * 8000
        stream.send(self.buffer, self.sent_data)

    def sent_data(self, stream, octets):
        stream.send(self.buffer, self.sent_data)

    def __del__(self):
        pass

if __name__ == "__main__":
    neubot.net.connect("127.0.0.1", "8009", connected=Source)
    neubot.net.loop()
