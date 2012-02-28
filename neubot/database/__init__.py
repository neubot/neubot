# neubot/database/__init__.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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

import logging
import sqlite3

from neubot.database import table_config
from neubot.database import table_geoloc
from neubot.database import table_log
from neubot.database import table_speedtest
from neubot.database import table_bittorrent
from neubot.database import migrate
from neubot.database import migrate2

from neubot import system

class DatabaseManager(object):
    def __init__(self):
        self.path = system.get_default_database_path()
        self.dbc = None

    def set_path(self, path):
        self.path = path

    def connect(self):
        self.connection()

    def connection(self):
        if not self.dbc:
            if self.path != ":memory:":
                self.path = system.check_database_path(self.path, logging.error)
            logging.debug("* Database: %s", self.path)
            self.dbc = sqlite3.connect(self.path)

            #
            # To avoid the need to map at hand columns in
            # a row with the sql schema, which is as error
            # prone as driving drunk.
            #
            self.dbc.row_factory = sqlite3.Row

            #
            # Migrate MUST be before table creation.  This
            # is safe because table creation always uses
            # the IF NOT EXISTS clause.  And this is needed
            # because otherwise we cannot migrate archived
            # databases (whose version number is old).
            # The exception is the config table which must
            # be present because migrate() looks at it.
            #
            table_config.create(self.dbc)

            migrate.migrate(self.dbc)
            migrate2.migrate(self.dbc)

            table_speedtest.create(self.dbc)
            table_geoloc.create(self.dbc)
            table_bittorrent.create(self.dbc)
            table_log.create(self.dbc)

        return self.dbc

DATABASE = DatabaseManager()
