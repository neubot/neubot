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

#
# Neubot database.
# Using sqlite3 because (among other things) there is support for
# concurrency and so we don't need to struggle to lock the database
# file.
#

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from collections import deque
from neubot.compat import deque_appendleft
from ConfigParser import SafeConfigParser
from StringIO import StringIO
from sqlite3 import connect
from getopt import GetoptError
from sqlite3 import Error
from neubot import version
from getopt import getopt
from os import environ
from neubot import log
from time import time
from sys import exit
from sys import stderr
from sys import stdout
from sys import argv

#
# Config table.
# The config table is like a dictionary and keeps some useful
# variables.  So far the only variable it keeps is the version
# of the database format, that might be useful in the future
# to convert an old database to a new one, should we change the
# format.
#

CONFIG_MAKE = "CREATE TABLE config(name TEXT PRIMARY KEY, value TEXT);"
CONFIG_FILL = "INSERT INTO config VALUES('version', '1.0');"

#
# Results table.
# Each result is a triple (tag, result, timestamp), where: the
# tag is the name of the test that produced the result, and is
# used to filter by producer; the result is the XML document
# that contains all the test-dependent fields; and the timestamp
# is used to filter just a subset of the results.
# We don't provide a fine-grained schema for the result because
# this instance of sqlite3 should only provide a convenient way
# to store the results on disk.
# XXX The query to prune the table is not very elegant because I
# was not able to find a better way to select the last N rows of
# a table.
#

RESULTS_MAKE        = """CREATE TABLE results(id INTEGER PRIMARY KEY,
                         tag TEXT, result TEXT, timestamp INTEGER);"""
RESULTS_PRUNE       = """DELETE FROM results WHERE id IN (
                         SELECT id FROM results LIMIT :count);"""
RESULTS_SAVE        = """INSERT INTO results VALUES(null, :tag,
                         :result, :timestamp);"""

#
# Prune.
# This operation guarantees that there are not more than MAXROWS
# in the database and will additionally invoke VACUUM to ensure
# that we don't waste any space.
# This might be convenient on the client side where probably the
# user does not want the neubot database to eat too much hard-disk
# space.
#

MAXROWS = 4096

#
# Database manager.
# This class manages the sqlite3 database and keeps an in-memory
# cache of the most recent results.  The User Interface API will
# access this cache when GET /api/results is invoked, to produce
# the response body.  So, the cache cache makes sense on client-
# side only, and is therefore disabled on server-side.
#

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.queue = deque()
        self.connection = None
        self._do_connect()
        self._autoprune()
        self._do_init_queue()

    #
    # Init
    #

    def _do_connect(self):
        log.debug("* Connecting to database: %s" % self.config.path)
        self.connection = connect(self.config.path)
        cursor = self.connection.cursor()
        self._make_config(cursor)
        self._make_results(cursor)
        cursor.close()

    #
    # XXX I don't known how the check whether a table already
    # exists, and so I code this poor-man solution where the
    # code tries to create the table and reads the exception
    # string to check whether the table already exists or not.
    # The possible issue here could be i18n.
    #

    def _make_config(self, cursor):
        try:
            cursor.execute(CONFIG_MAKE)
            cursor.execute(CONFIG_FILL)
            self.connection.commit()
        except Error, reason:
            if str(reason) != "table config already exists":
                raise

    def _make_results(self, cursor):
        try:
            cursor.execute(RESULTS_MAKE)
            self.connection.commit()
        except Error, reason:
            if str(reason) != "table results already exists":
                raise

    def _autoprune(self):
        if self.config.auto_prune:
            log.start("* Database auto-prune")
            self.prune()
            log.complete()

    #
    # XXX Assume that this is not going to be very slow
    # because the number of rows in the table is bounded
    # due to periodic prune() invocation.
    #

    def _do_init_queue(self):
        if self.config.client:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * from RESULTS;")
            for rowid, tag, result, t in cursor:
                deque_appendleft(self.queue, self.config.maxcache,
                                 (tag, result, t))
            cursor.close()

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

    def save_result(self, tag, result):
        t = int(time())
        cursor = self.connection.cursor()
        cursor.execute(RESULTS_SAVE, {"tag": tag,
          "result": result, "timestamp": t})
        self.connection.commit()
        cursor.close()
        if self.config.client:
            deque_appendleft(self.queue, self.config.maxcache,
                             (tag, result, t))

    def get_config(self):
        dictionary = {}
        cursor = self.connection.cursor()
        cursor.execute("SELECT * from config;")
        for key, value in cursor:
            dictionary[key] = value
        cursor.execute("SELECT COUNT(*) from results;")
        dictionary["results"] = cursor.fetchone()[0]
        dictionary["path"] = self.config.path
        cursor.close()
        return dictionary

    #
    # TODO get/iterate_results() access the database and
    # get_cached_results() access the cache, but they do
    # basically the same thing, and so it should be very
    # nice to hide these three functions behind the same
    # common interface.
    #

    def iterate_results(self, func):
        cursor = self.connection.cursor()
        cursor.execute("SELECT result FROM results;")
        for result in cursor:
            func(result)
        cursor.close()

    def get_results(self):
        vector = []
        self.iterate_results(vector.append)
        return vector

    #
    # This function is not going to be the fastest one
    # on earth for long queues (but on most cases we keep
    # the length bounded).
    # This function's arguments have the same semantic
    # of the built-in range() function when invoked with
    # two arguments, e.g. range(0,10).
    #

    def get_cached_results(self, filt=None, start=0, stop=-1):
        vector = []
        if self.queue:
            vector.append("<results>")
            if stop == -1:
                stop = len(self.queue)
            pos = 0
            for tag, result, t in self.queue:
                if pos == stop:
                    break
                if pos >= start and (not filt or filt == tag):
                    vector.append(result)
                pos = pos + 1
            vector.append("</results>")
        body = "".join(vector)
        stringio = StringIO(body)
        return stringio

    def prune(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM results;")
        count = int(cursor.fetchone()[0])
        if count > MAXROWS:
            count -= MAXROWS
            cursor.execute(RESULTS_PRUNE, {"count": count})
            cursor.execute("VACUUM;")
            self.connection.commit()
        cursor.close()

#
# [database]
# auto_prune = True
# maxcache = 256
# path = /var/neubot/database.sqlite3
# client = True
#

class DatabaseConfig(SafeConfigParser):
    def __init__(self):
        SafeConfigParser.__init__(self)
        self.auto_prune = True
        self.maxcache = 256
        self.path = "/var/neubot/database.sqlite3"
        self.client = True

    def readfp(self, fp, filename=None):
        SafeConfigParser.readfp(self, fp, filename)
        self._do_parse()

    def read(self, filenames):
        SafeConfigParser.read(self, filenames)
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

    def configure(self, filenames, fakerc):
        self.config.read(filenames)
        self.config.readfp(fakerc)
        # XXX other modules need to read() it too
        fakerc.seek(0)

    def start(self):
        self.dbm = DatabaseManager(self.config)

database = DatabaseModule()

#
# Test unit
#

USAGE =									\
"Usage: @PROGNAME@ -V\n"						\
"       @PROGNAME@ --help\n"						\
"       @PROGNAME@ [-ilvz] [-D name=value] [database]\n"

HELP = USAGE +								\
"Options:\n"								\
"  -D name=value : Set configuration file property.\n"			\
"  --help        : Print this help screen and exit.\n"			\
"  -i            : Create and init the specified database.\n"		\
"  -l            : List all the results in the database.\n"		\
"  -V            : Print version number and exit.\n"			\
"  -v            : Run the program in verbose mode.\n"			\
"  -z            : Compress database pruning old results.\n"

BRIEF, INIT, LIST, PRUNE = range(0,4)

def main(args):
    fakerc = StringIO()
    fakerc.write("[database]\n")
    action = BRIEF
    # parse
    try:
        options, arguments = getopt(args[1:], "D:ilVvz", ["help"])
    except GetoptError:
        stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        exit(1)
    # options
    for name, value in options:
        if name == "-D":
            fakerc.write(value + "\n")
        elif name == "--help":
            stdout.write(HELP.replace("@PROGNAME@", args[0]))
            exit(0)
        elif name == "-i":
            action = INIT
        elif name == "-l":
            action = LIST
        elif name == "-V":
            stdout.write(version + "\n")
        elif name == "-v":
            log.verbose()
        elif name == "-z":
            action = PRUNE
    # config
    filenames = ["/etc/neubot/config"]
    if environ.has_key("HOME"):
        filenames.append(environ["HOME"] + "/.neubot/config")
    fakerc.seek(0)
    database.configure(filenames, fakerc)
    # arguments
    if len(arguments) >= 2:
        stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        exit(1)
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
                stdout.write("%s\t: %s\n" % (key, config[key]))
        elif action == LIST:
            results = database.dbm.get_results()
            if results:
                stdout.write("<results>\n")
                for result in results:
                    stdout.write("%s\n" % result)
                stdout.write("</results>\n")
        elif action == PRUNE:
            database.dbm.prune()

if __name__ == "__main__":
    main(argv)
