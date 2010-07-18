# testing/utils.py
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

import errno
import fcntl
import logging
import os
import sys

import neubot

# ______________________________________________________________________

#
# To speed-up servers and clients we should wrap file descriptors
# with the following class (which, however, is not portable.)
#

from neubot.net.streams import *

class FdStream(Stream):
    def __init__(self, poller, fileno):
        Stream.__init__(self, poller, fileno, "", "")
        self.setblocking(False)

    def __del__(self):
        pass

    def setblocking(self, blocking):
        flags = fcntl.fcntl(self.fileno(), fcntl.F_GETFL)
        if blocking:
            flags &= ~os.O_NONBLOCK
        else:
            flags |= os.O_NONBLOCK
        fcntl.fcntl(self.fileno(), fcntl.F_SETFL, flags)

    def soclose(self):
        pass                                                            # ???

    def sorecv(self, maxlen):
        try:
            octets = os.read(self.fileno(), maxlen)
            return SUCCESS, octets
        except os.error, (code, reason):
            if code in [errno.EAGAIN, errno.EWOULDBLOCK]:
                return WANT_READ, ""
            else:
                neubot.utils.prettyprint_exception()
                return ERROR, ""

    def sosend(self, octets):
        try:
            count = os.write(self.fileno(), octets)
            return SUCCESS, count
        except os.error, (code, reason):
            if code in [errno.EAGAIN, errno.EWOULDBLOCK]:
                return WANT_WRITE, 0
            else:
                neubot.utils.prettyprint_exception()
                return ERROR, 0

# ______________________________________________________________________

from neubot.net.pollers import poller

class Echo:
    def __init__(self, stream):
        stream.recv(8000, self.got_data)

    def got_data(self, stream, octets):
        stream.send(octets, self.sent_data)

    def sent_data(self, stream, octets):
        stream.recv(8000, self.got_data)

    def __del__(self):
        pass

if __name__ == "__main__":
    Echo(FdStream(poller, 0))
    neubot.net.loop()
