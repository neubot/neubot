# neubot/backend.py

#
# Copyright (c) 2012-2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
#
# Copyright (c) 2012 Fabio Forno <fabio.forno@gmail.com>
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
import os
import sys
import time

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.compat import json

from neubot.backend_mlab import BackendMLab
from neubot.backend_neubot import BackendNeubot
from neubot.backend_null import BackendNull
from neubot.backend_volatile import BackendVolatile

from neubot.config import CONFIG

from neubot import utils_hier
from neubot import utils_path

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
        self.backend = BackendNeubot(self)
        self.vfs = None
        self.datadir = None
        self.passwd = None

        if os.name == "posix":
            from neubot import utils_posix
            self.vfs = utils_posix
        elif os.name == "nt":
            from neubot import utils_nt
            self.vfs = utils_nt
        else:
            raise RuntimeError("backend: no VFS available")

    def use_backend(self, name):
        ''' Use the specified backend for saving results '''
        logging.debug('backend: use backend: %s', name)
        if name == 'mlab':
            self.backend = BackendMLab(self)
        elif name == 'neubot':
            self.backend = BackendNeubot(self)
        elif name == 'null':
            self.backend = BackendNull(self)
        elif name == 'volatile':
            self.backend = BackendVolatile(self)
        else:
            raise RuntimeError('%s: No such backend' % name)

    @staticmethod
    def get_available_backends():
        ''' Returns available backends '''
        return ('mlab', 'neubot', 'null', 'volatile')

    def __getattr__(self, attr):
        ''' Route calls to the real backend '''
        return getattr(self.backend, attr)

    #
    # I adapted the following methods from the FileSystemPOSIX
    # class, which was contained by neubot/filesys_posix.py.
    #
    # The following code is here in the proxy, and not inside
    # any specific driver, because it is common to all drivers.
    #

    def really_init_datadir(self, uname=None, datadir=None):
        ''' Initialize datadir '''

        #
        # Note: this code is the implementation of datadir_init(),
        # which may be called by the backends that need it.
        #
        # The reason for this code structure is that some backends
        # (e.g., the volatile backend) don't need to initialize
        # the datadir, while others (e.g., the mlab backend) need
        # to initialize the datadir.
        #

        if datadir:
            self.datadir = datadir
        else:
            self.datadir = utils_hier.LOCALSTATEDIR
        logging.debug('backend: datadir: %s', self.datadir)

        logging.debug('backend: user name: %s', uname)
        if uname:
            self.passwd = self.vfs.getpwnam(uname)
        else:
            #
            # The common case (in which you don't override the
            # default user name with a custom name).
            #
            # XXX The following lines are the only piece of code
            # in this file that is heavily system dependent.
            #
            # Ideally it would be better to move the functionality
            # that they implement into system-specific files.
            #
            # BTW the lines below are so heavily system-dependent
            # because I adapted them from a POSIX-only file.
            #
            if os.name == "posix":
                from neubot import system_posix
                self.passwd = system_posix.getpwnam()
            elif os.name == "nt":
                from neubot import utils_nt
                self.passwd = utils_nt.PWEntry()
            else:
                raise RuntimeError("backend: unsupported system")

        logging.debug('backend: uid: %d', self.passwd.pw_uid)
        logging.debug('backend: gid: %d', self.passwd.pw_gid)

        #
        # Here we are assuming that the /var/lib (or /var) dir
        # exists and has the correct permissions.
        #
        # We are also assuming that we are running with enough privs
        # to be able to create a directory there on behalf of the
        # specified uid and gid.
        #
        logging.debug('backend: datadir init: %s', self.datadir)
        self.vfs.mkdir_idempotent(self.datadir, self.passwd.pw_uid,
                                  self.passwd.pw_gid)

    def datadir_touch(self, components):
        ''' Touch a file below datadir '''
        return utils_path.depth_visit(self.datadir, components, self._visit)

    def _visit(self, curpath, leaf):
        ''' Callback for depth_visit() '''
        if not leaf:
            logging.debug('backend: mkdir_idempotent: %s', curpath)
            self.vfs.mkdir_idempotent(curpath, self.passwd.pw_uid,
                                      self.passwd.pw_gid)
        else:
            logging.debug('backend: touch_idempotent: %s', curpath)
            self.vfs.touch_idempotent(curpath, self.passwd.pw_uid,
                                      self.passwd.pw_gid)

BACKEND = BackendProxy()

USAGE = '''\
usage: backend.py [-Fv] [-b backend] [-d datadir] [-m message] [-t time]
                        [-u user] [filesys-mode-args]'''

def main(args):
    ''' main function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'b:d:Fm:t:u:v')
    except getopt.error:
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
    filesys_mode = False
    msg = default_msg
    timestamp = None
    uname = None
    for name, value in options:
        if name == '-b':
            bcknd = value
        elif name == '-d':
            datadir = value
        elif name == "-F":
            filesys_mode = True
        elif name == '-m':
            msg = value
        elif name == '-t':
            timestamp = float(value)
        elif name == "-u":
            uname = value
        elif name == '-v':
            CONFIG['verbose'] = 1

    if bcknd:
        BACKEND.use_backend(bcknd)
    if msg != default_msg:
        msg = json.loads(msg)
    if timestamp:
        time.time = lambda: timestamp  # XXX

    BACKEND.datadir_init(uname=uname, datadir=datadir)

    if filesys_mode and arguments:
        BACKEND.datadir_touch(arguments)
        sys.exit(0)
    if arguments:
        sys.exit(USAGE)

    BACKEND.bittorrent_store(msg)
    BACKEND.speedtest_store(msg)
    BACKEND.store_raw(msg)
    BACKEND.store_generic("generictest", msg)

if __name__ == '__main__':
    main(sys.argv)
