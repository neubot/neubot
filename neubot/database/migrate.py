# neubot/database/migrate.py

#
# Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>
#  Universita` degli Studi di Milano
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

import logging
import uuid

from neubot.marshal import unmarshal_object

#
# Bump MINOR version number because we've added two
# fields to speedtest and bittorrent tables.  One
# is ``neubot_version`` that contains current Neubot
# version in numeric representation.  The other is
# ``platform`` that contains the current OS name.
#
def migrate_from__v4_0__to__v4_1(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT value FROM config WHERE name='version';")
    ver = cursor.fetchone()[0]
    if ver == "4.0":
        logging.info("* Migrating database from version 4.0 to 4.1")
        cursor.execute("""UPDATE config SET value='4.1'
                        WHERE name='version';""")

        cursor.execute("ALTER TABLE speedtest ADD platform TEXT;")
        cursor.execute("ALTER TABLE speedtest ADD neubot_version TEXT;")

        cursor.execute("ALTER TABLE bittorrent ADD platform TEXT;")
        cursor.execute("ALTER TABLE bittorrent ADD neubot_version TEXT;")

        connection.commit()
    cursor.close()

#
# Bump MAJOR version number because now we have also the
# 'log' table.  Do not create the table here because
# it is auto-created by the database initialization code
# that runs BEFORE us.
#
def migrate_from__v3_0__to__v4_0(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT value FROM config WHERE name='version';")
    ver = cursor.fetchone()[0]
    if ver == "3.0":
        logging.info("* Migrating database from version 3.0 to 4.0")
        cursor.execute("""UPDATE config SET value='4.0'
                        WHERE name='version';""")
        connection.commit()
    cursor.close()

#
# Bump MAJOR version number because now we have also the
# bittorrent table.  Do not create the table here because
# it is auto-created by the database initialization code
# that runs BEFORE us.
#
def migrate_from__v2_1__to__v3_0(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT value FROM config WHERE name='version';")
    ver = cursor.fetchone()[0]
    if ver == "2.1":
        logging.info("* Migrating database from version 2.1 to 3.0")
        cursor.execute("""UPDATE config SET value='3.0'
                        WHERE name='version';""")
        connection.commit()
    cursor.close()

#
# Bump version number because now we have also the geolocation
# table.  Do not create the table here because it is auto-created
# by the database initialization code, that runs before us.
# XXX Probably here it was a mistake 2.0 -> 2.1 and the correct
# version number should have been 3.0, because we've ADDED something
# to the database.  However now we cannot undo.
#
def migrate_from__v2_0__to__v2_1(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT value FROM config WHERE name='version';")
    ver = cursor.fetchone()[0]
    if ver == "2.0":
        logging.info("* Migrating database from version 2.0 to 2.1")
        cursor.execute("""UPDATE config SET value='2.1'
                        WHERE name='version';""")
        connection.commit()
    cursor.close()

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
        "uuid": obj.client,
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

# delete results table and create speedtest one
def migrate_from__v1_1__to__v2_0(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT value FROM config WHERE name='version';")
    ver = cursor.fetchone()[0]
    if ver == "1.1":
        logging.info("* Migrating database from version 1.1 to 2.0")
        connection.execute("""CREATE TABLE IF NOT EXISTS speedtest(
                id INTEGER PRIMARY KEY,
                timestamp INTEGER,
                uuid TEXT,
                internal_address TEXT,
                real_address TEXT,
                remote_address TEXT,
                connect_time NUMERIC,
                latency NUMERIC,
                download_speed NUMERIC,
                upload_speed NUMERIC,
                privacy_informed NUMERIC,
                privacy_can_collect NUMERIC,
                privacy_can_share NUMERIC
            );""")
        query = """INSERT INTO speedtest VALUES (
                null,
                :timestamp,
                :uuid,
                :internal_address,
                :real_address,
                :remote_address,
                :connect_time,
                :latency,
                :download_speed,
                :upload_speed,
                :privacy_informed,
                :privacy_can_collect,
                :privacy_can_share
            );"""
        cursor.execute("SELECT result, timestamp, uuid FROM results ORDER BY timestamp;")
        for result, timestamp, uuid in cursor:
            result = unmarshal_object(result, "application/xml",
                                      SpeedtestResultXML)
            result = speedtest_result_good_from_xml(result)
            result['timestamp'] = timestamp
            result['uuid'] = uuid
            result['privacy_informed'] = 0
            result['privacy_can_collect'] = 0
            result['privacy_can_share'] = 0
            connection.execute(query, result)
        connection.execute("DROP TABLE results;")
        connection.execute("""UPDATE config SET value='2.0'
                          WHERE name='version';""")
        connection.commit()

# add uuid to database
def migrate_from__v1_0__to__v1_1(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT value FROM config WHERE name='version';")
    ver = cursor.fetchone()[0]
    if ver == "1.0":
        logging.info("* Migrating database from version 1.0 to 1.1")
        cursor.execute("ALTER TABLE results ADD uuid TEXT;")
        cursor.execute("INSERT INTO config VALUES('uuid', :ident);",
                       {"ident": str(uuid.uuid4())})
        cursor.execute("""UPDATE config SET value='1.1'
                        WHERE name='version';""")
        connection.commit()
    cursor.close()

MIGRATORS = [
    migrate_from__v1_0__to__v1_1,
    migrate_from__v1_1__to__v2_0,
    migrate_from__v2_0__to__v2_1,
    migrate_from__v2_1__to__v3_0,
    migrate_from__v3_0__to__v4_0,
    migrate_from__v4_0__to__v4_1,
]

def migrate(connection):
    for migrator in MIGRATORS:
        migrator(connection)
