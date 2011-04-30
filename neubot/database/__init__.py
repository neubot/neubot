# neubot/database/__init__.py

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
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

#
# Neubot database.
# Using sqlite3 because (among other things) there is support for
# concurrency and so we don't need to struggle to lock the database
# file.
#

import ConfigParser
import StringIO
import collections
import getopt
import sqlite3
import sys
import uuid

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.compat import json
from neubot.database import table_config
from neubot.database import table_speedtest
from neubot.database.migrate import migrate
from neubot.log import LOG
from neubot.marshal import unmarshal_object
from neubot.utils import timestamp
from neubot.utils import get_uuid
from neubot import system

# Database manager.

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.ident = None
        self._do_connect()
        self._autoprune()
        migrate(self.connection)
        self._do_fetch_ident()

    #
    # Init
    #

    def _do_connect(self):
        LOG.debug("* Connecting to database: %s" % self.config.path)
        self.connection = sqlite3.connect(self.config.path)
        table_config.create(self.connection)
        table_speedtest.create(self.connection)

    def _autoprune(self):
        if self.config.auto_prune:
            self.prune()

    def _do_fetch_ident(self):
        if self.config.client:
            self.ident = table_config.dictionarize(self.connection)["uuid"]

    #
    # Finish
    #

    def _do_disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def __del__(self):
        self._do_disconnect()

    #
    # API
    #

    def save_result(self, obj):
        table_speedtest.insertxxx(self.connection, obj)

    def get_config(self):
        return table_config.dictionarize(self.connection)

    def query_results_json(self, since=-1, until=-1):
        octets = table_speedtest.jsonize(self.connection, since, until)
        stringio = StringIO.StringIO(octets)
        return stringio

    def prune(self):
        table_speedtest.prune(self.connection)

    def delete(self):
        table_speedtest.prune(self.connection, until=timestamp())

    def rebuild_uuid(self):
        table_config.update(self.connection, {"uuid": get_uuid()}.iteritems())

#
# [database]
# auto_prune = True
# maxcache = 256
# path = /var/neubot/database.sqlite3
# client = True
#

class DatabaseConfig(ConfigParser.SafeConfigParser):
    def __init__(self):
        ConfigParser.SafeConfigParser.__init__(self)
        self.auto_prune = True
        self.maxcache = 256
        self.path = system.get_default_database_path()
        self.client = True

    def readfp(self, fp, filename=None):
        ConfigParser.SafeConfigParser.readfp(self, fp, filename)
        self._do_parse()

    def read(self, filenames):
        ConfigParser.SafeConfigParser.read(self, filenames)
        self._do_parse()

    def _do_parse(self):
        if self.has_option("database", "maxcache"):
            self.maxcache = self.getint("database", "maxcache")
            if self.maxcache < 0:
                raise ValueError("database.maxcache must not be negative")
        if self.has_option("database", "auto_prune"):
            self.auto_prune = self.getboolean("database", "auto_prune")
        if self.has_option("database", "client"):
            self.client = self.getboolean("database", "client")
        if self.has_option("database", "path"):
            self.path = self.get("database", "path")

class DatabaseModule:
    def __init__(self):
        self.config = DatabaseConfig()
        self.dbm = None

    def set_path(self, path):
        self.config.path = path

    def connect(self):
        self.start()

    def connection(self):
        return self.dbm.connection

    def configure(self, filenames, fakerc):
        self.config.read(filenames)
        self.config.readfp(fakerc)
        # XXX other modules need to read() it too
        fakerc.seek(0)

    def start(self):
        self.config.path = system.check_database_path(self.config.path)
        self.dbm = DatabaseManager(self.config)

DATABASE = database = DatabaseModule()

#
# Test unit
#

USAGE =									\
"Usage: @PROGNAME@ -V\n"						\
"       @PROGNAME@ --help\n"						\
"       @PROGNAME@ [-dfilvz] [-D name=value] [database]\n"

HELP = USAGE +								\
"Options:\n"								\
"  -D name=value : Set configuration file property.\n"			\
"  --help        : Print this help screen and exit.\n"			\
"  -d            : Delete all the results in the database.\n"		\
"  -f            : Rebuild neubot unique identifier.\n"			\
"  -i            : Create and init the specified database.\n"		\
"  -l            : List all the results in the database.\n"		\
"  -V            : Print version number and exit.\n"			\
"  -v            : Run the program in verbose mode.\n"			\
"  -z            : Compress database pruning old results.\n"

BRIEF, DELETE, INIT, LIST, PRUNE, REBUILD = range(0,6)

VERSION = "0.3.6"

def main(args):
    fakerc = StringIO.StringIO()
    fakerc.write("[database]\n")
    action = BRIEF
    # parse
    try:
        options, arguments = getopt.getopt(args[1:], "D:dfilVvz", ["help"])
    except getopt.GetoptError:
        sys.stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        sys.exit(1)
    # options
    for name, value in options:
        if name == "-D":
            fakerc.write(value + "\n")
        elif name == "-d":
            action = DELETE
        elif name == "--help":
            sys.stdout.write(HELP.replace("@PROGNAME@", args[0]))
            sys.exit(0)
        elif name == "-f":
            action = REBUILD
        elif name == "-i":
            action = INIT
        elif name == "-l":
            action = LIST
        elif name == "-V":
            sys.stdout.write(VERSION + "\n")
        elif name == "-v":
            LOG.verbose()
        elif name == "-z":
            action = PRUNE
    # config
    fakerc.seek(0)
    # arguments
    if len(arguments) >= 2:
        sys.stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        sys.exit(1)
    elif len(arguments) == 1:
        database.config.path = arguments[0]
    # run
    database.start()
    if action == INIT:
        # nothing to do
        pass
    else:
        if action == BRIEF:
            config = database.dbm.get_config()
            for key in sorted(config.keys()):
                sys.stdout.write("%s\t: %s\n" % (key, config[key]))
        elif action == DELETE:
            database.dbm.delete()
        elif action == LIST:
            results = database.dbm.query_results_json()
            if results:
                sys.stdout.write(results.read())
                sys.stdout.write("\n")
        elif action == PRUNE:
            database.dbm.prune()
        elif action == REBUILD:
            database.dbm.rebuild_uuid()

if __name__ == "__main__":
    main(sys.argv)
