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

import uuid
from neubot.log import LOG
from neubot.marshal import unmarshal_object

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
        LOG.info("* Migrating database from version 1.1 to 2.0")
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
        LOG.info("* Migrating database from version 1.0 to 1.1")
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
]

def migrate(connection):
    for migrator in MIGRATORS:
        migrator(connection)
