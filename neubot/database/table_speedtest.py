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

'''
 Manage the speedtest table.
'''

from neubot.database import _table_utils
from neubot import utils

TEMPLATE = {
    "timestamp": 0,
    "uuid": "",
    "internal_address": "",
    "real_address": "",
    "remote_address": "",

    "privacy_informed": 0,
    "privacy_can_collect": 0,
    "privacy_can_publish": 0,

    "connect_time": 0.0,
    "download_speed": 0.0,
    "upload_speed": 0.0,
    "latency": 0.0,

    "platform": "",
    "neubot_version": "",

    # Added Neubot 0.4.12
    "test_version": 1,
}

CREATE_TABLE = _table_utils.make_create_table("speedtest", TEMPLATE)
INSERT_INTO = _table_utils.make_insert_into("speedtest", TEMPLATE)

def create(connection, commit=True):
    ''' Create a new speedtest table '''
    connection.execute(CREATE_TABLE)
    if commit:
        connection.commit()

def insert(connection, dictobj, commit=True, override_timestamp=True):
    ''' Insert a result dictionary into speedtest table '''
    _table_utils.do_insert_into(connection, INSERT_INTO, dictobj, TEMPLATE,
                                commit, override_timestamp)

def listify(connection, since=-1, until=-1):
    ''' Converts the content of speedtest table into a list '''
    vector = []
    cursor = connection.cursor()
    query = _table_utils.make_select("speedtest", TEMPLATE,
                                     since=since, until=until,
                                     desc=True)
    cursor.execute(query, {"since": since, "until": until})
    for row in cursor:
        vector.append(dict(row))
    return vector

def prune(connection, until=None, commit=True):
    ''' Removes old results from the table '''
    if not until:
        until = utils.timestamp() - 365 * 24 * 60 * 60
    connection.execute("DELETE FROM speedtest WHERE timestamp < ?;", (until,))
    if commit:
        connection.commit()
