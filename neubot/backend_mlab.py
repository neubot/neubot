# neubot/backend_mlab.py

#
# Copyright (c) 2012
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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

''' M-Lab backend '''

#
# Follows closely the M-Lab specification for saving results
# in a very scalable way.
#

import gzip
import time

from neubot.compat import json

from neubot.backend_null import BackendNull

class BackendMLab(BackendNull):
    ''' M-Lab backend '''

    def bittorrent_store(self, message):
        ''' Saves the results of a bittorrent test '''
        self.do_store('bittorrent', message)

    def store_raw(self, message):
        ''' Saves the results of the RAW test '''
        self.do_store('raw', message)

    def speedtest_store(self, message):
        ''' Saves the results of a speedtest test '''
        self.do_store('speedtest', message)

    def store_generic(self, test, results):
        """ Store the results of a generic test """
        self.do_store(test, results)

    def do_store(self, test, message):
        ''' Saves the results of the given test '''

        # Get time information
        thetime = time.time()
        gmt = time.gmtime(thetime)
        nanosec = int((thetime % 1.0) * 1000000000)

        #
        # Build path components.
        # The time format is ISO8601, except that we use nanosecond
        # and not microsecond precision.
        #
        components = [
                      time.strftime('%Y', gmt),
                      time.strftime('%m', gmt),
                      time.strftime('%d', gmt),
                      '%s.%09dZ_%s.gz' % (
                        time.strftime('%Y%m%dT%H:%M:%S', gmt),
                        nanosec, test)
                     ]

        #
        # Make sure that the path exists and that ownership
        # and permissions are OK.
        #
        fullpath = self.proxy.datadir_touch(components)

        #
        # Open the output file for appending, write into
        # it the message and close.
        # We open for appending just in case two tests
        # terminates at the same time (unlikely!).
        #
        filep = gzip.open(fullpath, 'ab')
        json.dump(message, filep)
        filep.close()

    def walk_generic(self, test, index):
        """ Walk over the results of a generic test """
        return []

    def datadir_init(self, uname=None, datadir=None):
        ''' Initialize datadir (if needed) '''
        self.proxy.really_init_datadir(uname, datadir)
