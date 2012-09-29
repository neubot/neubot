# neubot/listener.py

#
# Copyright (c) 2010-2012 Simone Basso <bassosimone@gmail.com>,
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

''' Pollable socket listener '''

# Adapted from neubot/net/stream.py
# Python3-ready: yes

from neubot.pollable import Pollable
from neubot.poller import POLLER

class Listener(Pollable):

    ''' Pollable socket listener '''

    def __init__(self, parent, sock, endpoint, sslconfig, sslcert):
        Pollable.__init__(self)
        self.parent = parent
        self.lsock = sock
        self.endpoint = endpoint
        self.sslconfig = sslconfig
        self.sslcert = sslcert

        # Want to listen "forever"
        self.watchdog = -1

        POLLER.set_readable(self)
        self.parent.handle_listen(self)

    def __repr__(self):
        return str(self.endpoint)

    def fileno(self):
        return self.lsock.fileno()

    def handle_read(self):
        # Make sure we route exceptions properly
        try:
            sock = self.lsock.accept()[0]
            sock.setblocking(False)
            self.parent.handle_accept(self, sock, self.sslconfig, self.sslcert)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.parent.handle_accept_error(self)

    def handle_close(self):
        self.parent.handle_listen_close(self)
