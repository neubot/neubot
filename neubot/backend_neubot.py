# neubot/backend_neubot.py

#
# Copyright (c) 2012-2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN),
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

''' Neubot backend '''

#
# The traditional Neubot backend, which saves results into
# an sqlite3 database.  Codesigned with Alessio Palmero Aprosio
# and with comments and feedback from Roberto D'Auria.
#

import logging
import os

try:
    import cPickle as pickle
except ImportError:
    import pickle

from neubot.database import DATABASE
from neubot.database import table_bittorrent
from neubot.database import table_speedtest
from neubot.database import table_raw

from neubot.backend_null import BackendNull

from neubot import utils_path

SPLIT_INTERVAL = 1024
SPLIT_NUM_FILES = 15

class BackendNeubot(BackendNull):
    ''' Neubot backend '''

    def __init__(self, proxy):
        BackendNull.__init__(self, proxy)
        self.generic = {}

    def bittorrent_store(self, message):
        ''' Saves the results of a bittorrent test '''
        DATABASE.connect()
        if DATABASE.readonly:
            logging.warning('backend_neubot: readonly database')
            return
        table_bittorrent.insert(DATABASE.connection(), message)

    def store_raw(self, message):
        ''' Saves the results of a raw test '''
        DATABASE.connect()
        if DATABASE.readonly:
            logging.warning('backend_neubot: readonly database')
            return
        table_raw.insert(DATABASE.connection(), message)

    def speedtest_store(self, message):
        ''' Saves the results of a speedtest test '''
        DATABASE.connect()
        if DATABASE.readonly:
            logging.warning('backend_neubot: readonly database')
            return
        table_speedtest.insert(DATABASE.connection(), message)

    #
    # 'Generic' load/store functions. We append test results into a vector,
    # which is also serialized to disk using pickle. When the number of
    # items in the vector exceeds a threshold, we rotate the logfiles created
    # using pickle, and we start over with an empty vector.
    #
    # Also we access results by index, as the Twitter API does. Each index
    # is the number of a logfile. When there is no index, we serve the logfile
    # that is currently being written.
    #
    # Dash Elhauge had the original idea behind this implementation, my
    # fault if it took too much to implement it.
    #

    def store_generic(self, test, results):
        """ Store the results of a generic test """

        components = [ "%s.pickle" % test ]
        fullpath = self.proxy.datadir_touch(components)

        # Load
        if not test in self.generic:
            filep = open(fullpath, "rb")
            content = filep.read()
            filep.close()
            if content:
                self.generic[test] = pickle.loads(content)
            else:
                self.generic[test] = []

        # Rotate
        if len(self.generic[test]) >= SPLIT_INTERVAL:

            tmppath = fullpath + "." + str(SPLIT_NUM_FILES)
            if os.path.isfile(tmppath):
                os.unlink(tmppath)

            for index in range(SPLIT_NUM_FILES, 0, -1):
                srcpath = fullpath + "." + str(index - 1)
                if not os.path.isfile(srcpath):
                    continue
                destpath = fullpath + "." + str(index)
                os.rename(srcpath, destpath)

            tmppath = fullpath + ".0"
            filep = open(tmppath, "wb")
            pickle.dump(self.generic[test], filep)
            filep.close()
            self.generic[test] = []

        # Write
        self.generic[test].append(results)
        filep = open(fullpath, "wb")
        pickle.dump(self.generic[test], filep)
        filep.close()

    def walk_generic(self, test, index):
        """ Walk over the results of a generic test """

        filename = "%s.pickle" % test
        if index != None:
            filename += "." + str(int(index))

        fullpath = utils_path.append(self.proxy.datadir, filename, False)
        if not fullpath:
            return []

        if not os.path.isfile(fullpath):
            return []

        filep = open(fullpath, "rb")
        content = filep.read()
        filep.close()

        if not content:
            return []

        return pickle.loads(content)

    def datadir_init(self, uname=None, datadir=None):
        ''' Initialize datadir (if needed) '''
        self.proxy.really_init_datadir(uname, datadir)
