# neubot/listener.py

#
# Copyright (c) 2010-2012, 2014
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     Simone Basso <bassosimone@gmail.com>.
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
# Adapted from neubot/net/stream.py
# pylint: disable = missing-docstring
# Python3-ready: yes
#

import logging

from neubot.pollable import Pollable
from neubot.poller import POLLER

from neubot import utils_net

class Acceptor(Pollable):

    def __init__(self, poller, sock):
        Pollable.__init__(self)
        self.sock = sock
        self.clear_timeout()  # Listen "forever"
        logging.debug("Acceptor: wait for READABLE")
        poller.set_readable(self)

    def fileno(self):
        return self.sock.fileno()

    def handle_read(self):
        logging.debug("Acceptor: is READABLE")
        # Make sure we route exceptions properly
        try:
            sock = self.sock.accept()[0]
            sock.setblocking(False)
            logging.debug("Acceptor: accepted fileno %d", sock.fileno())
            self.handle_accept(sock)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.warning("Acceptor: Unhandled exception", exc_info=1)
            self.handle_accept_error()

    def handle_accept(self, sock):
        pass

    def handle_accept_error(self):
        pass

    def handle_close(self):
        pass

class Listener(Acceptor):  # Used by neubot/handler.py

    def __init__(self, parent, sock, endpoint, sslconfig, sslcert):
        Acceptor.__init__(self, POLLER, sock)
        self.parent = parent
        self.endpoint = endpoint  # Not actually used
        self.sslconfig = sslconfig
        self.sslcert = sslcert
        self.parent.handle_listen(self)

    def handle_accept(self, sock):
        self.parent.handle_accept(self, sock, self.sslconfig, self.sslcert)

    def handle_accept_error(self):
        self.parent.handle_accept_error(self)

    def handle_close(self):
        self.parent.handle_listen_close(self)

class StreamAcceptor(Acceptor):

    def __init__(self, parent, poller, sock):
        self.parent = parent
        Acceptor.__init__(self, poller, sock)

    def handle_accept(self, sock):
        self.parent.handle_accept(sock)

class StreamListener(object):

    def __init__(self, poller):
        self.poller = poller

    def listen(self, family, address, port):

        logging.debug("StreamListener: %s, '%s', %s", family, address, port)
        logging.debug("StreamListener: resolve_list")

        addrinfos = utils_net.resolve_list(family, "SOCK_STREAM",
          address, port, "AI_PASSIVE")
        if not addrinfos:
            logging.warning("StreamListener: resolve_list FAIL")
            return 0

        logging.debug("StreamListener: resolve_list OK")

        count = 0
        for ainfo in addrinfos:
            logging.debug("StreamListener: listen_ainfo %s", ainfo)
            sock = utils_net.listen_ainfo(ainfo)
            if not sock:
                logging.debug("StreamListener: listen_ainfo FAIL")
                continue

            logging.debug("StreamListener: listen_ainfo OK")
            StreamAcceptor(self, self.poller, sock)
            count += 1

        logging.debug("StreamListener: bound sockets %d", count)
        return count

    def handle_accept(self, sock):
        pass
