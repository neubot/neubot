# neubot/database/migrate.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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
#        _               _
#  _ __ (_)__ _ _ _ __ _| |_ ___
# | '  \| / _` | '_/ _` |  _/ -_)
# |_|_|_|_\__, |_| \__,_|\__\___|
#         |___/
#
# code to migrate from one version to another
#

import uuid
from neubot.log import LOG

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
        cursor.execute("INSERT INTO config VALUES('uuid', :ident);",
                       {"ident": str(uuid.uuid4())})
        connection.commit()
    cursor.close()

MIGRATORS = [
    migrate_from__v1_0__to__v1_1,
]

def migrate(connection):
    for migrator in MIGRATORS:
        migrator(connection)
