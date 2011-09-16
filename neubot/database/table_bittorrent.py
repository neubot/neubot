# neubot/database/table_bittorrent.py

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

#
# Algorithms to create and manage the SQL table required
# by the BitTorrent test.
#

from neubot.database import _table_utils

from neubot import compat
from neubot import utils

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

    "neubot_version": "",
    "platform": "",
}

CREATE_TABLE = _table_utils.make_create_table("bittorrent", TEMPLATE)
INSERT_INTO = _table_utils.make_insert_into("bittorrent", TEMPLATE)

def create(connection, commit=True):
    connection.execute(CREATE_TABLE)
    if commit:
        connection.commit()

# Override timestamp on server-side to guarantee consistency
def insert(connection, dictobj, commit=True, override_timestamp=True):
    _table_utils.do_insert_into(connection, INSERT_INTO, dictobj, TEMPLATE,
                                commit, override_timestamp)

def walk(connection, func, since=-1, until=-1):
    cursor = connection.cursor()
    SELECT = _table_utils.make_select("bittorrent", TEMPLATE,
      since=since, until=until, desc=True)
    cursor.execute(SELECT, {"since": since, "until": until})
    return map(func, cursor)

def listify(connection, since=-1, until=-1):
    return walk(connection, lambda t: dict(t), since, until)

def prune(connection, until=None, commit=True):
    if not until:
        until = utils.timestamp() - 365 * 24 * 60 * 60
    connection.execute("DELETE FROM bittorrent WHERE timestamp < ?;", (until,))
    if commit:
        connection.commit()
