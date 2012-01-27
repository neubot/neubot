# neubot/backend.py

#
# Copyright (c) 2012 Fabio Forno <fabio.forno@gmail.com>
# Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
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

''' Backend API '''

#
# Generic backend for saving results, so that we can switch transparently
# between different real backends.
#
# The 'neubot' backend saves the result into an sqlite3 database and
# is typically used on the user side.
#
# The 'mlab' backend follows Measurement Lab conventions and each test
# is a compressed JSON file in a given directory.
#
# Prototype code for this file discussed with and written by Fabio
# Forno, thanks!
#

import getopt
import logging
import sys
import time

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.filesys import FILESYS
from neubot.compat import json

from neubot.backend_mlab import BackendMLab
from neubot.backend_neubot import BackendNeubot
from neubot.backend_null import BackendNull

class BackendProxy(object):
    ''' Proxy for the real backend '''

    #
    # Quoting from <http://docs.python.org/reference/datamodel.html>:
    #
    # > Class instances
    # > A class instance is created by calling a class object (see
    # > above). A class instance has a namespace implemented as a
    # > dictionary which is the first place in which attribute references
    # > are searched. When an attribute is not found there, and the
    # > instance's class has an attribute by that name, the search
    # > continues with the class attributes. If a class attribute is
    # > found [...]
    # > If no class attribute is found, and the object's class has a
    # > __getattr__() method, that is called to satisfy the lookup.
    #
    # So, this means that __getattr__() is invoked only for methods
    # and/or attributes that are not defined in this class.
    #

    def __init__(self):
        ''' Initialize backend proxy '''
        self.backend = BackendNeubot()

    def use_backend(self, name):
        ''' Use the specified backend for saving results '''
        logging.debug('backend: use backend: %s', name)
        if name == 'mlab':
            self.backend = BackendMLab()
        elif name == 'neubot':
            self.backend = BackendNeubot()
        elif name == 'null':
            self.backend = BackendNull()
        else:
            raise RuntimeError('%s: No such backend' % name)

    @staticmethod
    def get_available_backends():
        ''' Returns available backends '''
        return ('mlab', 'neubot', 'null')

    def __getattr__(self, attr):
        ''' Route calls to the real backend '''
        return getattr(self.backend, attr)

BACKEND = BackendProxy()

USAGE = '''\
Usage: backend.py [-v] [-b backend] [-d datadir] [-m message] [-t time]'''

def main(args):
    ''' main function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'b:d:m:t:v')
    except getopt.error:
        sys.exit(USAGE)
    if arguments:
        sys.exit(USAGE)

    # Good-enough default message
    default_msg = {
        "timestamp": 0,
        "uuid": "",
        "internal_address": "",
        "real_address": "",
        "remote_address": "",

        "privacy_informed": 0,
        "privacy_can_collect": 0,
        "privacy_can_publish": 0,

        "latency": 0.0,
        "connect_time": 0.0,
        "download_speed": 0.0,
        "upload_speed": 0.0,

        "neubot_version": "",
        "platform": "",
    }

    bcknd = None
    datadir = None
    msg = default_msg
    timestamp = None
    for name, value in options:
        if name == '-b':
            bcknd = value
        elif name == '-d':
            datadir = value
        if name == '-m':
            msg = value
        elif name == '-t':
            timestamp = float(value)
        elif name == '-v':
            logging.getLogger().setLevel(logging.DEBUG)

    if bcknd:
        BACKEND.use_backend(bcknd)
    if datadir:
        FILESYS.datadir = datadir
    if msg != default_msg:
        msg = json.loads(msg)
    if timestamp:
        time.time = lambda: timestamp

    FILESYS.datadir_init()

    BACKEND.bittorrent_store(msg)
    BACKEND.speedtest_store(msg)

if __name__ == '__main__':
    main(sys.argv)
