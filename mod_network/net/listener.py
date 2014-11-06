# net/listener.py

#
# Copyright (c) 2010-2012, 2014
#   Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#   and Simone Basso <bassosimone@gmail.com>.
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

""" Stream listener """

from neubot.pollable import Pollable

class Listener(Pollable):

    """ TCP Stream listener """

    def __init__(self, poller, parent, sock, endpoint):
        Pollable.__init__(self)
        self._poller = poller
        self._parent = parent
        self._lsock = sock
        self._endpoint = endpoint

    def __repr__(self):
        return "Listener(%s)" % str(self._endpoint)

    def listen(self):
        """ Start listening """
        self._poller.set_readable(self)
        self._parent.started_listening(self)

    def fileno(self):  # Part of the Pollable object model
        return self._lsock.fileno()

    #
    # Catch all types of exception because an error in
    # connection_made() MUST NOT cause the server to stop
    # listening for new connections.
    #
    def handle_read(self):  # Part of the Pollable object model
        try:
            sock = self._lsock.accept()[0]
            sock.setblocking(False)
            self._parent.connection_made(sock, self._endpoint, 0)
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as exception:
            self._parent.accept_failed(self, exception)
            return

    def handle_close(self):  # Part of the Pollable object model
        raise RuntimeError("Unexpected event")

    def handle_write(self):  # Part of the Pollable object model
        raise RuntimeError("Unexpected event")

    def handle_periodic(self, timenow):  # Part of the Pollable object model
        return False  # Never stop listening

    def set_timeout(self, timeo):  # Part of the Pollable object model
        raise RuntimeError("Setting timeout not supported")
