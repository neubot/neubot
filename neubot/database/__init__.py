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
import getopt
import os.path
import sqlite3
import sys
import types
import uuid

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.times import timestamp
from neubot.compat import deque_appendleft
from neubot.marshal import unmarshal_object
from neubot.compat import json
from neubot.log import LOG

from neubot.system import want_rw_file

#
# Config table.
# The config table is like a dictionary and keeps some useful
# variables.  It keeps the version of the database format, that
# might be useful in the future to convert an old database to
# a new one, should we change the format.
#
# <on uuid and privacy>
# It also keeps an unique identifier for each neubot client
# which we believe would help data analysis, e.g. we could
# review the measurement history of a given neubot looking for
# certain patterns, such as the connection speed decreasing
# near the end of the month because the user exceeded a
# bandwidth cap.
#
# We believe this should have a negligible impact on privacy
# because it would, at most, allow to say that neubot XYZ owner
# changed IP address, and hence, possibly, provider and/or
# location (and note that this information is functional to
# our goal of building a network neutrality map organized by
# geographic location and provider).
#
# So, we believe you should not be concerned by this issue,
# but, in case you were, the way to go is `neubot database -f`
# that forces neubot to generate and use A NEW uuid.
# </on uuid and privacy>
#

CONFIG_MAKE = "CREATE TABLE config(name TEXT PRIMARY KEY, value TEXT);"
CONFIG_UPDATE_UUID = "UPDATE config SET value=:ident WHERE name='uuid';"
CONFIG_FILL_UUID = "INSERT INTO config VALUES('uuid', :ident);"
CONFIG_FILL_VERSION = "INSERT INTO config VALUES('version', '1.1');"

#
# Results table.
# Each result is a tuple (tag, result, timestamp, uuid), where:
# tag is the name of the test that produced the result, and is
# used to filter by producer; the result is the XML document
# that contains all the test-dependent fields; timestamp is used
# to filter just a subset of the results; and uuid is the unique
# identifier of the client.
# We don't provide a fine-grained schema for the result because
# this instance of sqlite3 should only provide a convenient way
# to store the results on disk.
# XXX The query to prune the table is not very elegant because I
# was not able to find a better way to select the last N rows of
# a table.
#

RESULTS_MAKE        = """CREATE TABLE results(id INTEGER PRIMARY KEY,
                         tag TEXT, result TEXT, timestamp INTEGER,
                         uuid TEXT);"""
RESULTS_PRUNE       = """DELETE FROM results WHERE id IN (
                         SELECT id FROM results LIMIT :count);"""
RESULTS_SAVE        = """INSERT INTO results VALUES(null, :tag,
                         :result, :timestamp, :ident);"""

#
# Prune.
# This operation guarantees that there are not more than MAXROWS
# in the database and will additionally invoke VACUUM to ensure
# that we don't waste any space.
# This might be convenient on the client side where probably the
# user does not want the neubot database to eat too much hard-disk
# space.
#

MAXROWS = 103680

#
#        _               _
#  _ __ (_)__ _ _ _ __ _| |_ ___
# | '  \| / _` | '_/ _` |  _/ -_)
# |_|_|_|_\__, |_| \__,_|\__\___|
#         |___/
#
# code to migrate from one version to another
#

# add uuid to database
def migrate_from__v1_0__to__v1_1(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT value FROM config WHERE name='version';")
    ver = cursor.fetchone()[0]
    if ver == "1.0":
        LOG.info("* Migrating database from version 1.0 to 1.1")
        cursor.execute("ALTER TABLE results ADD uuid TEXT;")
        cursor.execute("""UPDATE config SET value='1.1'
                          WHERE name='version';""")
        cursor.execute(CONFIG_FILL_UUID, {"ident": str(uuid.uuid4())})
        connection.commit()
    cursor.close()

MIGRATORS = [
    migrate_from__v1_0__to__v1_1,
]

def migrate(connection):
    for migrator in MIGRATORS:
        migrator(connection)

#
# XXX XXX XXX
# BEGIN code to marshal/unmarshal
# The purpose of the code below is to allow easy marshalling and
# unmarshalling of the speedtest results using the facilities provided
# by <neubot/marshal.py>.  This code will gone when all the results
# in the database will be stored as pure SQL rather than as XML.
#

class SpeedtestResultXML(object):
    def __init__(self):
        self.client = ""
        self.timestamp = 0.0            #XXX
        self.internalAddress = ""
        self.realAddress = ""
        self.remoteAddress = ""
        self.connectTime = 0.0
        self.latency = 0.0
        self.downloadSpeed = 0.0
        self.uploadSpeed = 0.0

def speedtest_result_good_from_xml(obj):
    dictionary = {
        "client_uuid": obj.client,
        "timestamp": int(float(obj.timestamp)),         #XXX
        "internal_address": obj.internalAddress,
        "real_address": obj.realAddress,
        "remote_address": obj.remoteAddress,
        "connect_time": obj.connectTime,
        "latency": obj.latency,
        "download_speed": obj.downloadSpeed,
        "upload_speed": obj.uploadSpeed,
    }
    return dictionary

# END code to marshal/unmarshal
# XXX XXX XXX


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
        want_rw_file(self.config.path)
        self.connection = sqlite3.connect(self.config.path)
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
            cursor.execute(CONFIG_FILL_VERSION)
            cursor.execute(CONFIG_FILL_UUID, {"ident": str(uuid.uuid4())})
            self.connection.commit()
        except sqlite3.Error, reason:
            if str(reason) != "table config already exists":
                raise

    def _make_results(self, cursor):
        try:
            cursor.execute(RESULTS_MAKE)
            self.connection.commit()
        except sqlite3.Error, reason:
            if str(reason) != "table results already exists":
                raise

    def _autoprune(self):
        if self.config.auto_prune:
            self.prune()

    def _do_fetch_ident(self):
        if self.config.client:
            cursor = self.connection.cursor()
            cursor.execute("SELECT value FROM config WHERE name='uuid';")
            self.ident = cursor.fetchone()[0]
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

    def save_result(self, tag, result, ident):
        t = timestamp()
        cursor = self.connection.cursor()
        cursor.execute(RESULTS_SAVE, {"tag": tag, "result": result,
                       "timestamp": t, "ident": ident})
        self.connection.commit()
        cursor.close()

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

    def query_results_functional(self, func, tag=None, since=-1,
                                 until=-1, uuid_=None):
        if since < 0:
            since = 0
        if until < 0:
            until = timestamp()
        params = {"tag": tag, "since": since, "until": until, "uuid": uuid_}
        cursor = self.connection.cursor()
        query = """SELECT result, timestamp FROM results
          WHERE timestamp >= :since AND timestamp < :until"""
        if tag:
            query += " AND tag = :tag"
        if uuid_:
            query += " AND uuid = :uuid"
        query += ";"
        cursor.execute(query, params)
        for result in cursor:
            func(result[0])
        cursor.close()

    def query_results_json(self, tag=None, since=-1, until=-1, uuid_=None):
        vector = []
        self.query_results_functional(vector.append, tag, since, until, uuid_)

        if vector:
            temp, vector = vector, []
            for octets in temp:
                result = unmarshal_object(octets, "application/xml",
                                          SpeedtestResultXML)
                result = speedtest_result_good_from_xml(result)
                vector.append(result)

        octets = json.dumps(vector, ensure_ascii=True)
        stringio = StringIO.StringIO(octets)
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

    def delete(self):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM results;")
        cursor.close()
        self.connection.commit()

    def rebuild_uuid(self):
        cursor = self.connection.cursor()
        cursor.execute(CONFIG_UPDATE_UUID, {"ident": str(uuid.uuid4())})
        cursor.close()
        self.connection.commit()

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
        self.path = "neubot.sqlite3"
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
