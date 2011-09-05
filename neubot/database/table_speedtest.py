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

from neubot.database import _table_utils
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

TEMPLATE = {
    "timestamp": 0,
    "uuid": "",
    "internal_address": "",
    "real_address": "",
    "remote_address": "",

    "privacy_informed": 0,
    "privacy_can_collect": 0,
    "privacy_can_share": 0,

    "connect_time": 0.0,
    "download_speed": 0.0,
    "upload_speed": 0.0,
    "latency": 0.0,
}

CREATE_TABLE = _table_utils.make_create_table("speedtest", TEMPLATE)
INSERT_INTO = _table_utils.make_insert_into("speedtest", TEMPLATE)

def create(connection, commit=True):
    connection.execute(CREATE_TABLE)
    if commit:
        connection.commit()

# Override timestamp on server-side to guarantee consistency
def insert(connection, dictobj, commit=True, override_timestamp=True):
    if override_timestamp:
        dictobj['timestamp'] = utils.timestamp()
    connection.execute(INSERT_INTO, dictobj)
    if commit:
        connection.commit()

def insertxxx(connection, obj, commit=True, override_timestamp=True):
    insert(connection, obj_to_dict(obj), commit, override_timestamp)

def walk(connection, func, since=-1, until=-1):
    cursor = connection.cursor()
    SELECT = _table_utils.make_select("speedtest", TEMPLATE,
      since=since, until=until, desc=True)
    cursor.execute(SELECT, {"since": since, "until": until})
    return map(func, cursor)

def listify(connection, since=-1, until=-1):
    return walk(connection, lambda t: dict(t), since, until)

def prune(connection, until=None, commit=True):
    if not until:
        until = utils.timestamp() - 365 * 24 * 60 * 60
    connection.execute("DELETE FROM speedtest WHERE timestamp < ?;", (until,))
    if commit:
        connection.commit()
