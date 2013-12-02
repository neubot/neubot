# neubot/poller_libneubot.py

#
# Copyright (c) 2013
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
# Python3-ready: yes
# pylint: disable = C0111, R0923, W0212
#

import ctypes
import os
import sys

# XXX: hardcoded search paths
sys.path.insert(0, "/usr/local/share/libneubot")
sys.path.insert(0, "/usr/share/libneubot")

from libneubot import LIBNEUBOT
from libneubot import NEUBOT_POLLER_CALLBACK

from neubot.poller_interface import PollableInterface
from neubot.poller_interface import PollerInterface

def _handle_read_ok(pyobject):
    pollable = ctypes.cast(pyobject, ctypes.py_object).value
    pollable.defer_read = 0  # For robustness, forget it immediately
    pollable.handle_read()

def _handle_read_timeout(pyobject):
    pollable = ctypes.cast(pyobject, ctypes.py_object).value
    pollable.defer_read = 0  # Clear here to avoid double free in close()
    pollable.close()

HANDLE_READ_OK = NEUBOT_POLLER_CALLBACK(_handle_read_ok)
HANDLE_READ_TIMEOUT = NEUBOT_POLLER_CALLBACK(_handle_read_timeout)

def _handle_write_ok(pyobject):
    pollable = ctypes.cast(pyobject, ctypes.py_object).value
    pollable.defer_write = 0  # For robustness, forget it immediately
    pollable.handle_write()

def _handle_write_timeout(pyobject):
    pollable = ctypes.cast(pyobject, ctypes.py_object).value
    pollable.defer_write = 0  # Clear here to avoid double free in close()
    pollable.close()

HANDLE_WRITE_OK = NEUBOT_POLLER_CALLBACK(_handle_write_ok)
HANDLE_WRITE_TIMEOUT = NEUBOT_POLLER_CALLBACK(_handle_write_timeout)

class PollableLibneubot(PollableInterface):

    def __init__(self, poller):
        PollableInterface.__init__(self, poller)
        self.poller = poller
        self.defer_read = 0
        self.defer_write = 0
        self.filenum = -1
        self.timeout = 300.0

    def attach(self, filenum):
        self.filenum = filenum

    def detach(self):
        self.filenum = -1

    # TODO: make the code robust wrt filenum == -1?

    def fileno(self):
        return self.filenum

    def set_readable(self):
        if self.defer_read != 0:
            return
        self.defer_read = LIBNEUBOT.NeubotPoller_defer_read(self.poller.handle,
          self.filenum, HANDLE_READ_OK, HANDLE_READ_TIMEOUT, self, self.timeout)
        if self.defer_read == 0:
            os._exit(1)
        self.poller.set_readable_(self)

    def unset_readable(self):
        if self.defer_read == 0:
            return
        LIBNEUBOT.NeubotEvent_cancel(self.defer_read)
        self.poller.unset_readable_(self)
        self.defer_read = 0

    def handle_read(self):
        pass

    def set_writable(self):
        if self.defer_write != 0:
            return
        self.defer_write = LIBNEUBOT.NeubotPoller_defer_write(
          self.poller.handle, self.filenum, HANDLE_WRITE_OK,
          HANDLE_WRITE_TIMEOUT, self, self.timeout)
        if self.defer_write == 0:
            os._exit(1)
        self.poller.set_writable_(self)

    def unset_writable(self):
        if self.defer_write == 0:
            return
        LIBNEUBOT.NeubotEvent_cancel(self.defer_write)
        self.poller.unset_writable_(self)
        self.defer_write = 0

    def handle_write(self):
        pass

    def set_timeout(self, delta):
        self.timeout = delta

    def clear_timeout(self):
        self.timeout = 3600  # FIXME

    def handle_periodic(self):
        pass  # FIXME

    def close(self):
        self.unset_readable()
        self.unset_writable()
        self.handle_close()

    def handle_close(self):
        pass

def _handle_callback(pyobject):
    poller, pytuple = pyobject
    poller.handle_callback_(pytuple)

HANDLE_CALLBACK = NEUBOT_POLLER_CALLBACK(_handle_callback)

class PollerLibneubot(PollerInterface):

    def __init__(self):
        PollerInterface.__init__(self)
        self.handle = LIBNEUBOT.NeubotPoller_construct()
        self.readset = set()
        self.writeset = set()
        self.callbacks = {}

    def sched(self, delta, function, argument):
        pytuple = function, argument
        self.callbacks[pytuple] = 1
        pyobject = (self, pytuple)
        LIBNEUBOT.NeubotPoller_sched(self.handle, delta,
          HANDLE_CALLBACK, pyobject)

    def _handle_callback(self, pytuple):
        del self.callbacks[pytuple]
        function, argument = pytuple
        function(argument)

    def loop(self):
        LIBNEUBOT.NeubotPoller_loop(self.handle)

    def break_loop(self):
        LIBNEUBOT.NeubotPoller_break_loop(self.handle)

    def set_readable_(self, pollable):
        self.readset.add(pollable)

    def unset_readable_(self, pollable):
        self.readset.remove(pollable)

    def set_writable_(self, pollable):
        self.writeset.add(pollable)

    def unset_writable_(self, pollable):
        self.writeset.remove(pollable)
