# neubot/network/pollers.py
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
import logging
import select
import time

import neubot

class poller:
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.periodic = set()
        self.funcs = set()
        self.readset = {}
        self.writeset = {}

    def register_periodic(self, periodic):
        self.periodic.add(periodic)

    def unregister_periodic(self, periodic):
        if periodic in self.periodic:
            self.periodic.remove(periodic)

    def register_func(self, func):
        self.funcs.add(func)

    def register_initializer(self, init):
        logging.warning("poller.register_initializer is deprecated")
        self.funcs.add(init)

    def set_readable(self, connection):
        self.readset[connection.fileno()] = connection

    def set_writable(self, connection):
        self.writeset[connection.fileno()] = connection

    def unset_readable(self, connection):
        if self.readset.has_key(connection.fileno()):
            del self.readset[connection.fileno()]

    def unset_writable(self, connection):
        if self.writeset.has_key(connection.fileno()):
            del self.writeset[connection.fileno()]

    def close(self, connection):
        try:
            self.unset_readable(connection)
            self.unset_writable(connection)
            connection.closing()
        except:
            neubot.prettyprint_exception()

    def _readable(self, fileno):
        if self.readset.has_key(fileno):        # XXX
            connection = self.readset[fileno]
            try:
                connection.readable()
            except:
                neubot.prettyprint_exception()
                self.close(connection)

    def _writable(self, fileno):
        if self.writeset.has_key(fileno):        # XXX
            connection = self.writeset[fileno]
            try:
                connection.writable()
            except:
                neubot.prettyprint_exception()
                self.close(connection)

    def loop(self):
        last = time.time()
        while True:
            if self.funcs:
                for func in self.funcs:
                    try:
                        func()
                    except:
                        neubot.prettyprint_exception()
                self.funcs.clear()
            if not (self.readset or self.writeset or self.periodic):
                break
            try:
                res = select.select(self.readset.keys(),
                    self.writeset.keys(), [], self.timeout)
            except select.error, (code, reason):
                if code == errno.EINTR:
                    continue
                neubot.prettyprint_exception()
                break
            except:
                neubot.prettyprint_exception()
                break
            for fileno in res[0]:
                self._readable(fileno)
            for fileno in res[1]:
                self._writable(fileno)
            now = time.time()
            if now - last >= self.timeout:
                for periodic in self.periodic:
                    try:
                        periodic(now)
                    except:
                        neubot.prettyprint_exception()
                last = now
