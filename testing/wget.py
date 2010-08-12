# testing/wget.py
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

#
# A very stripped-down wget(1)
#

import sys
if __name__ == "__main__":
    sys.path.insert(0, ".")

import neubot

def received(message):
    sys.stdout.write(message.body.read())

def sent(message):
    neubot.http.recv(message, received=received)

if __name__ == "__main__":
    uri = sys.argv[1]
    message = neubot.http.compose(method="GET", uri=uri, keepalive=False)
    neubot.http.send(message, sent=sent)
    neubot.net.loop()
