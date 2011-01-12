# neubot/bittorrent/handler.py

#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by Greg Hazel
# Modified for neubot by Simone Basso <bassosimone@gmail.com>
#

class Handler(object):
    def connection_starting(self, addr):
        pass

    def connection_made(self, s):
        pass

    def connection_failed(self, s, exception):
        pass

    def data_came_in(self, addr, data):
        pass

    def connection_flushed(self, s):
        pass

    def connection_lost(self, s):
        pass

class StreamWrapper(object):
    def __init__(self, stream):
        self.handler = None
        self.stream = stream
        self.stream.notify_closing = self._closing
        self.ip, self.port = stream.peername[:2]
        self.port = int(self.port)
        self.closed = False

    def write(self, data):
        if self.closed:
            return
        # bleh
        if isinstance(data, buffer):
            data = str(data)
        self.stream.send(data, self._written)

    def _written(self, stream, data):
        self.handler.connection_flushed(self)

    def close(self):
        if self.closed:
            return
        self.stream.close()

    def _closing(self):
        self.closed = True
        self.handler.connection_lost(self, None)
        self.handler = None
        self.stream.notify_closing = None
        self.ip, self.port = None, None
        self.stream = None

    def attach_connector(self, handler):
        self.handler = handler
        self.stream.recv(8000, self._data_came_in)

    def _data_came_in(self, stream, data):
        self.handler.data_came_in((self.ip, self.port), data)
        if self.closed:
            return
        self.stream.recv(8000, self._data_came_in)
