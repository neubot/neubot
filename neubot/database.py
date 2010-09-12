# neubot/database.py
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
import os
import sys

import neubot

from neubot.compat import deque_appendleft

class database:
    def __init__(self):
        self.outfile = sys.stdout
        self.queue = collections.deque()

    def export(self):
        result = []
        for line in self.queue:
            result.append(line)
        return result

    def init(self, configparser):
        if configparser.has_option("DEFAULT", "database.path"):
            path = configparser.get("DEFAULT", "database.path")
            try:
                if path != "-":
                    #
                    # We don't lock the database file because we append
                    # the current date and time to the file name skele-
                    # ton in bin/*/neubot--and so it seems very unlike-
                    # ly that we open two files with the same name.
                    #
                    f = open(path, "ab")
                    self.outfile = f
                    if os.isatty(sys.stderr.fileno()):
                        sys.stderr.write("Database file: %s\n" % path)
            except IOError:
                logging.warning("Could not open database.path %s" % path)
                logging.warning("Using standard output instead")
                logging.warning("Here's the error that occurred:")
                neubot.utils.prettyprint_exception(write=logging.warning)

    def writes(self, octets):
        deque_appendleft(self.queue, 100, octets)
        self.outfile.write(octets)
        self.outfile.write("\r\n")
        self.outfile.flush()

instance = database()

export = instance.export
init = instance.init
writes = instance.writes
