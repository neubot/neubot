# neubot/whitelist.py
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

import collections
import logging

import neubot

TIMEOUT = 15

class whitelist:
    def __init__(self):
        self.dictionary = {}

    def __len__(self):
        return len(self.dictionary.keys())

    def allowed(self, address):
        return self.dictionary.has_key(address)

    #
    # FIXME The code below is a crap--yes, it allows a client to
    # run more than one Neubot instance, but the way this is im-
    # plemented sucks.  Rather than allowing on a per-IP address
    # basis, we should employ the unique identifier for the mea-
    # surement (we can use cookies for HTTP, infohashes for Bit-
    # Torrent, and so forth) together with the client IP address.
    #

    def register(self, address):
        if self.dictionary.has_key(address):
            count, ticks = self.dictionary[address]
        else:
            count = 0
        self.dictionary[address] = (count + 1, neubot.utils.ticks())
        logging.debug("Added address %s to whitelist" % address)

    def prune(self, now):
        stale = collections.deque()
        for address, (count, ticks) in self.dictionary.items():
            if now - ticks > TIMEOUT:
                stale.append(address)
        for address in stale:
            del self.dictionary[address]
            logging.debug("Removing (stale) address %s from whitelist" % address)

    def unregister(self, address):
        if self.dictionary.has_key(address):
            count, ticks = self.dictionary[address]
            count = count - 1
            if count == 0:
                del self.dictionary[address]
                logging.debug("Removed address %s from whitelist" % address)
            else:
                self.dictionary[address] = (count, ticks)

instance = whitelist()

allowed = instance.allowed
length = instance.__len__
register = instance.register
prune = instance.prune
unregister = instance.unregister
