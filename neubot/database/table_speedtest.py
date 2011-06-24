# neubot/database/table_speedtest.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
# Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>,
#  Universita` degli Studi di Milano
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

import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot import compat
from neubot import utils

#
# FIXME The following function glues the speedtest code and
# the database code.  The speedtest code passes downstream a
# an object with the following problems:
#
# 1. the timestamp _might_ be a floating because old
#    neubot clients have this bug;
#
def obj_to_dict(obj):
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
        "privacy_informed": obj.privacy_informed,
        "privacy_can_collect": obj.privacy_can_collect,
        "privacy_can_share": obj.privacy_can_share,
    }
    return dictionary

#
# TODO Here and below we should use the facilities provided
# by the new _table_utils.py helper file.
#
def create(connection, commit=True):
    connection.execute("""CREATE TABLE IF NOT EXISTS speedtest(
      id INTEGER PRIMARY KEY, timestamp INTEGER, uuid TEXT,
      internal_address TEXT, real_address TEXT, remote_address TEXT,
      connect_time NUMERIC, latency NUMERIC, download_speed NUMERIC,
      upload_speed NUMERIC, privacy_informed NUMERIC,
      privacy_can_collect NUMERIC, privacy_can_share NUMERIC);""")
    if commit:
        connection.commit()

# Override timestamp on server-side to guarantee consistency
def insert(connection, dictobj, commit=True, override_timestamp=True):
    if override_timestamp:
        dictobj['timestamp'] = utils.timestamp()
    connection.execute("""INSERT INTO speedtest VALUES (
      null, :timestamp, :uuid, :internal_address, :real_address,
      :remote_address, :connect_time, :latency, :download_speed,
      :upload_speed, :privacy_informed, :privacy_can_collect,
      :privacy_can_share);""", dictobj)
    if commit:
        connection.commit()

def insertxxx(connection, obj, commit=True, override_timestamp=True):
    insert(connection, obj_to_dict(obj), commit, override_timestamp)

def select_query(since, until):
    query = ["SELECT * FROM speedtest"]
    if since >= 0 or until >= 0:
        query.append(" WHERE ")
        if since >= 0:
            query.append("timestamp >= :since")
        if since >= 0 and until >= 0:
            query.append(" AND ")
        if until >= 0:
            query.append("timestamp < :until")
    query.append(" ORDER BY timestamp DESC")
    query.append(";")
    return "".join(query)

def walk(connection, func, since=-1, until=-1):
    cursor = connection.cursor()
    cursor.execute(select_query(since, until), locals())
    return map(func, cursor)

#
# TODO Now the tuple t is sqlite3.Row so we can avoid to
# do the mapping at hand.
#
def listify(connection, since=-1, until=-1):
    return walk(connection, lambda t: { "timestamp": t[1], "uuid": t[2],
      "internal_address": t[3], "real_address": t[4], "remote_address": t[5],
      "connect_time": t[6], "latency": t[7], "download_speed": t[8],
      "upload_speed": t[9], "privacy_informed": t[10],
      "privacy_can_collect": t[11], "privacy_can_share": t[12], },
      since, until)

def prune(connection, until=None, commit=True):
    if not until:
        until = utils.timestamp() - 365 * 24 * 60 * 60
    connection.execute("DELETE FROM speedtest WHERE timestamp < ?;", (until,))
    if commit:
        connection.commit()

if __name__ == "__main__":
    from neubot.speedtest.gen import ResultIterator
    import sqlite3, pprint

    connection = sqlite3.connect(":memory:")
    create(connection)
    create(connection)

    v = map(None, ResultIterator())
    for d in v:
        insert(connection, d, override_timestamp=False)

    v1 = listify(connection)
    if v != v1:
        raise RuntimeError

    since = utils.timestamp() - 7 * 24 * 60 * 60
    until = utils.timestamp() - 3 * 24 * 60 * 60
    v2 = listify(connection, since=since, until=until)
    if len(v2) >= len(v):
        raise RuntimeError

    prune(connection, until)
    pprint.pprint(listify(connection))
