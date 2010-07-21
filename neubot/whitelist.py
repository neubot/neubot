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
        #
        # FIXME In some (legitimate!) cases the measure is not performed
        # because a white-listing strategy that is based only on the IP
        # address seems to be too aggressive.  As a temporary work-around
        # I disable the mechanism so that we do not forbid legitimate
        # measurements.
        #
        #return self.dictionary.has_key(address)
        return True

    def register(self, address):
        self.dictionary[address] = neubot.utils.ticks()
        logging.debug("Added address %s to whitelist" % address)

    def prune(self, now):
        stale = collections.deque()
        for address, ticks in self.dictionary.items():
            if now - ticks > TIMEOUT:
                stale.append(address)
        for address in stale:
            del self.dictionary[address]
            logging.debug("Removing (stale) address %s from whitelist" % address)

    def unregister(self, address):
        if self.dictionary.has_key(address):
            del self.dictionary[address]
            logging.debug("Removed address %s from whitelist" % address)

instance = whitelist()

allowed = instance.allowed
length = instance.__len__
register = instance.register
prune = instance.prune
unregister = instance.unregister
