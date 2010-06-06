# neubot/table.py
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
import json
import logging
import time

TIMEOUT = 15

class resultsentry:
    def __init__(self, identifier, peername, timestamp):
        self.identifier = identifier
        self.peername = peername
        self.timestamp = timestamp
        self.concurrency = -1
        self.direction = ""
        self.length = -1
        self.myname = ""
        self.protocol = ""
        self.timespan = 0

    def __str__(self):
        dictionary = {}
        dictionary["concurrency"] = self.concurrency
        dictionary["direction"] = self.direction
        dictionary["identifier"] = self.identifier
        dictionary["length"] = self.length
        dictionary["myname"] = self.myname
        dictionary["peername"] = self.peername
        dictionary["protocol"] = self.protocol
        dictionary["timespan"] = self.timespan
        dictionary["timestamp"] = self.timestamp
        return json.dumps(dictionary, ensure_ascii=True)

class resultstable:
    def __init__(self):
        self.dictionary = {}

    def create_entry(self, identifier, peername):
        if self.dictionary.has_key(identifier):
            now = time.time()
            entry = self.dictionary[identifier]
            if now - entry.timestamp <= TIMEOUT:
                logging.warning("Entry already exists %s" % identifier)
                return False
            logging.info("Replacing (stale) entry %s" % identifier)
        entry = resultsentry(identifier, peername, time.time())
        self.dictionary[identifier] = entry
        logging.info("Created entry %s" % identifier)
        return True

    # XXX Assuming that we have 1:1 identifier:peername
    def find_identifier(self, peername):
        for identifier, entry in self.dictionary.items():
            if entry.peername == peername:
                return identifier
        return None

    def remove_entry(self, identifier):
        if self.dictionary.has_key(identifier):
            del self.dictionary[identifier]
            logging.info("Removed entry %s" % identifier)

    def prune(self, now):
        stale = collections.deque()
        for identifier, entry in self.dictionary.items():
            if now - entry.timestamp > TIMEOUT:
                stale.append(identifier)
        for identifier in stale:
            del self.dictionary[identifier]
            logging.info("Removed (stale) entry %s" % identifier)

    def stringify_entry(self, identifier):
        if not self.dictionary.has_key(identifier):
            raise Exception("Entry does not exist %s" % identifier)
        entry = self.dictionary[identifier]
        return str(entry)

    def update_entry(self, identifier, concurrency, direction, length,
                     myname, protocol, timespan):
        if self.dictionary.has_key(identifier):
            logging.info("Updating entry %s" % identifier)
            entry = self.dictionary[identifier]
            entry.concurrency = concurrency
            entry.direction = direction
            entry.length = length
            entry.myname = myname
            entry.protocol = protocol
            entry.timespan = timespan

instance = resultstable()

create_entry = instance.create_entry
find_identifier = instance.find_identifier
remove_entry = instance.remove_entry
prune = instance.prune
stringify_entry = instance.stringify_entry
update_entry = instance.update_entry
