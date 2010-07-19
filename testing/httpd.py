# testing/httpd.py
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
# A very stripped-down httpd(1)
#

import StringIO, neubot

def received(message):
    m = None
    if message.uri[0] == "/" and "../" not in message.uri:
        try:
            m = neubot.http.reply(message, code="200", reason="Ok",
                                  keepalive=False, mimetype="text/plain",
                                  body=open(message.uri[1:], "rb"))
        except IOError:
            pass
    if not m:
        m = neubot.http.reply(message, code="500", keepalive=False,
                              reason="Internal Server Error")
    neubot.http.send(m)

if __name__ == "__main__":
    message = neubot.http.compose(address="0.0.0.0", port="8080")
    neubot.http.recv(message, received=received)
    neubot.net.loop()
