# neubot/database/table_raw.py

#
# Copyright (c) 2011-2012
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
#
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
 Algorithms to create and manage the SQL table required
 by the RAW test.
'''

# Adapted from neubot/database/table_bittorrent.py

from neubot.compat import json
from neubot.database import _table_utils

from neubot import utils

#
# Currently Neubot always puts the timestamp on the X axis.  To implement that
# it suffices to have a |timestamp|json_data| table.  Still, I decided to add
# more fields for a mixture of two reasons: (i) in the future it's possible that
# we decide to SELECT over different attributes, e.g. real address; and (ii) to
# keep this table schema consistent with the one of existing tables.  Another
# difference is that we don't store privacy information: since 0.4.6 Neubot does
# not allow users to run tests unless all privacy permissions are given, so the
# privacy information is always (1,1,1) for other tests.
#
TEMPLATE = {
    "timestamp": 0,
    "uuid": "",
    "internal_address": "",
    "real_address": "",
    "remote_address": "",

    "connect_time": 0.0,
    "latency": 0.0,
    "download_speed": 0.0,

    "neubot_version": "",
    "platform": "",
    "json_data": "",
}

def __json_to_mapped_row(result):
    ''' Fill mapped row with result dictionary '''
    return {
            'timestamp': result['server']['goodput']['ticks'],
            'uuid': result['client']['uuid'],
            'internal_address': result['client']['myname'],
            'real_address': result['server']['peername'],
            'remote_address': result['server']['myname'],
            'neubot_version': result['client']['version'],
            'platform': result['client']['platform'],
            'connect_time': result['client']['connect_time'],
            'latency': result['client']['alrtt_avg'],
            'download_speed': (result['client']['goodput']['bytesdiff'] /
                               result['client']['goodput']['timediff']),
            'json_data': json.dumps(result),
           }

CREATE_TABLE = _table_utils.make_create_table('raw', TEMPLATE)
INSERT_INTO = _table_utils.make_insert_into('raw', TEMPLATE)

def create(connection, commit=True):
    ''' Create the RAW table '''
    connection.execute(CREATE_TABLE)
    if commit:
        connection.commit()

def insert(connection, dictobj, commit=True, override_timestamp=True):
    ''' Insert a result into RAW table '''
    dictobj = __json_to_mapped_row(dictobj)
    _table_utils.do_insert_into(connection, INSERT_INTO, dictobj, TEMPLATE,
                                commit, override_timestamp)

def listify(connection, since=-1, until=-1):
    ''' Converts to list the content of RAW table '''
    vector = []
    cursor = connection.cursor()
    query = _table_utils.make_select('raw', TEMPLATE,
                                     since=since, until=until,
                                     desc=True)
    cursor.execute(query, {"since": since, "until": until})
    for row in cursor:
        vector.append(dict(row))
    return vector

def prune(connection, until=None, commit=True):
    ''' Removes old results from RAW table '''
    if not until:
        until = utils.timestamp() - 365 * 24 * 60 * 60
    connection.execute('DELETE FROM raw WHERE timestamp < ?;', (until,))
    if commit:
        connection.commit()
