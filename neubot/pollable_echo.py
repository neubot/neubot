# neubot/pollable_echo.py

#
# Copyright (c) 2014
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>.
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
# pylint: disable = missing-docstring
#

import logging
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.listener import StreamListener
from neubot.pollable import AsyncStream
from neubot.pollable import SocketWrapper
from neubot.pollable import SSLHandshaker
from neubot.pollable import SSLWrapper
from neubot.poller import POLLER

MAXREAD = 1 << 18

class EchoStream(AsyncStream):

    def on_data(self, octets):
        logging.debug("EchoStream << %d bytes", len(octets))
        self.write(octets)

    def on_flush(self, count, complete):
        logging.debug("EchoStream >> %d bytes", count)
        if not complete:
            return
        self.read(MAXREAD)

class EchoListenerPlain(StreamListener):

    def handle_accept(self, sock):
        stream = EchoStream(self.poller, SocketWrapper(sock))
        stream.read(MAXREAD)

class EchoListenerSSL(StreamListener):

    def handle_accept(self, sock):
        deferred = SSLHandshaker.handshake(self.poller, sock,
          True, "cert.pem")
        deferred.add_callback(self.handle_accept_ssl)
        deferred.add_errback(self.handle_ssl_fail)

    def handle_accept_ssl(self, sslsock):
        stream = EchoStream(self.poller, SSLWrapper(sslsock))
        stream.read(MAXREAD)

    def handle_ssl_fail(self, exception):
        logging.warning("SSL handshake failed: %s", exception)

def main():
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    listener = EchoListenerPlain(POLLER)
    count = listener.listen("PF_UNSPEC6", "", "54321")
    if count <= 0:
        sys.exit("EchoListenerPlain: cannot listen")

    listener = EchoListenerSSL(POLLER)
    count = listener.listen("PF_UNSPEC6", "", "54322")
    if count <= 0:
        sys.exit("EchoListenerPlain: cannot listen")

    POLLER.loop()

if __name__ == "__main__":
    main()
