# neubot/database/migrate2.py

#
# Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>,
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

''' Migrate database from one version to another.  This module takes
    care of migration from version 4.2 of the schema onwards. '''

import asyncore
import logging
import re
import sqlite3
import sys
import uuid

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.database import _table_utils

# ===================
# Migrate: 4.2 -> 4.3
# ===================

class MigrateFrom42To43(object):

    ''' Migrate from 4.2 to 4.3 '''

    def __init__(self):

        ''' Initialize '''

        #  _____               _      _
        # |_   _|__ _ __  _ __| |__ _| |_ ___ ___
        #   | |/ -_) '  \| '_ \ / _` |  _/ -_|_-<
        #   |_|\___|_|_|_| .__/_\__,_|\__\___/__/
        #                |_|
        #
        # Here we have the templates for bittorrent and speedtest
        # as they were with schema version 4.1.
        # We have also the original mapping that was used in the
        # migration from schema 4.1 to 4.2, which was renaming the
        # privacy_can_share column to privacy_can_publish.
        # It is crucial here, of course, not to change the order
        # of the fields in the templates below.
        #

        bittorrent_template = {
            'timestamp': 0,
            'uuid': '',
            'internal_address': '',
            'real_address': '',
            'remote_address': '',

            'privacy_informed': 0,
            'privacy_can_collect': 0,
            'privacy_can_share': 0,

            'connect_time': 0.0,
            'download_speed': 0.0,
            'upload_speed': 0.0,

            'neubot_version': '',
            'platform': '',
        }

        speedtest_template = {
            'timestamp': 0,
            'uuid': '',
            'internal_address': '',
            'real_address': '',
            'remote_address': '',

            'privacy_informed': 0,
            'privacy_can_collect': 0,
            'privacy_can_share': 0,

            'connect_time': 0.0,
            'download_speed': 0.0,
            'upload_speed': 0.0,
            'latency': 0.0,

            'platform': '',
            'neubot_version': '',
        }

        mapping = { 'privacy_can_share': 'privacy_can_publish' }

        #  _  _              _                  _      _
        # | \| |_____ __ __ | |_ ___ _ __  _ __| |__ _| |_ ___ ___
        # | .` / -_) V  V / |  _/ -_) '  \| '_ \ / _` |  _/ -_|_-<
        # |_|\_\___|\_/\_/   \__\___|_|_|_| .__/_\__,_|\__\___/__/
        #                                 |_|
        #
        # Here we generate the bad and good new templates using the
        # code in _table_utils.
        # The bad new template is the one that was used in the broken
        # migration, PROVIDED THAT the version of Python and the system
        # architecture have not changed.
        # The good template is the one that should have been used in
        # the first place.
        #

        bittorrent_ntemplate_bad = _table_utils.rename_column_ntemplate(
                                                  bittorrent_template,
                                                  mapping,
                                                  broken=True)

        bittorrent_ntemplate_good = _table_utils.rename_column_ntemplate(
                                                   bittorrent_template,
                                                   mapping,
                                                   broken=False)

        speedtest_ntemplate_bad = _table_utils.rename_column_ntemplate(
                                                 speedtest_template,
                                                 mapping,
                                                 broken=True)

        speedtest_ntemplate_good = _table_utils.rename_column_ntemplate(
                                                  speedtest_template,
                                                  mapping,
                                                  broken=False)

        #  ___                       _
        # / __|_ __ ____ _ _ __ _ __(_)_ _  __ _ ___
        # \__ \ V  V / _` | '_ \ '_ \ | ' \/ _` (_-<
        # |___/\_/\_/\__,_| .__/ .__/_|_||_\__, /__/
        #                 |_|  |_|         |___/
        #
        # Here we compile the swappings tables, which tell us, given
        # a column, what column SHOULD contain the proper value for
        # it.  Of course, this is true only if the above-generated new
        # templates equals the ones generated during 4.1 -> 4.2.
        #

        self.bittorrent_swappings = [
          tpl for tpl in zip(
            bittorrent_ntemplate_bad,
            bittorrent_ntemplate_good
          )
        ]

        self.speedtest_swappings = [
          tpl for tpl in zip(
            speedtest_ntemplate_bad,
            speedtest_ntemplate_good
          )
        ]

        #
        # Keep track of the fields where we expect to have integers
        # and floats.  All other fields are strings.
        #

        self.integers = ( 'privacy_informed', 'privacy_can_collect',
                          'privacy_can_publish', 'timestamp' )

        self.floats = ( 'latency', 'download_speed', 'upload_speed',
                        'connect_time' )

    #  ___                _                _
    # | _ \___ ___ _ _ __| |___ _ _ ___ __| |
    # |   / -_) _ \ '_/ _` / -_) '_/ -_) _` |
    # |_|_\___\___/_| \__,_\___|_| \___\__,_|
    #
    # Here we define the function that will tell us whether it
    # seems that a given row (or part of it) was reordered.
    # When the reordering happens in a group of values that look
    # like the same, it is not possible to detect it.
    #

    @staticmethod
    def _reordered_timestamp(value):
        ''' reordered if not an integer and before 13 feb 2009 '''
        try:
            value = int(value)
        except ValueError:
            return True
        return value < 1234567890

    @staticmethod
    def _reordered_uuid(value):
        ''' reordered if not a uuid '''
        try:
            uuid.UUID(value)
        except ValueError:
            return True
        return False

    @staticmethod
    def _reordered_address(value):
        ''' reordered it does not look like IPv4 '''
        return not re.match(
          '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$',
          value)

    @staticmethod
    def _reordered_privacy(value):
        ''' reordered if neither zero nor one '''
        return not re.match('^[0-1]$', value)

    @staticmethod
    def _reordered_connect_time(value):
        ''' reordered if not float or greater than 40000 seconds '''
        try:
            value = float(value)
        except ValueError:
            return True
        #
        # This is an upper bound of all connections time I was
        # able to observe in Neubot datasets.  I hope it is big
        # enough to catch all connection times, but still able
        # to distinguish between a connection time and reordered
        # speed.
        #
        return value >= 40000

    @staticmethod
    def _reordered_speed(value):
        ''' reordered if not float '''
        try:
            float(value)
        except ValueError:
            return True
        return False

    @staticmethod
    def _reordered_version(value):
        ''' reordered if does not match version regex '''
        # version may not be set 
        if value == 'None' or value == '':
            return False
        return not re.match('^[0-9]+\.[0-9]{9}$', value)

    @staticmethod
    def _reordered_platform(value):
        ''' reordered if is not a supported platform '''
        # platform may not be set 
        if value == 'None' or value == '':
            return False
        for prefix in (
                       'linux',
                       'win32',
                       'cygwin',
                       'darwin',
                       'os2',
                       'os2emx',
                       'riscos',
                       'atheos',
                       'freebsd',
                       'openbsd',
                       'netbsd',
                      ):
            if value.startswith(prefix):
                return False
        return True

    def _seems_reordered(self, row):
        ''' Returns true if we believe the row was reordered '''

        count = 0

        # Stringify because we don't know the sqlite3-converted type
        count += self._reordered_timestamp(str(row['timestamp']))
        count += self._reordered_uuid(str(row['uuid']))
        count += self._reordered_platform(str(row['platform']))
        count += self._reordered_version(str(row['neubot_version']))
        count += self._reordered_privacy(str(row['privacy_informed']))
        count += self._reordered_privacy(str(row['privacy_can_collect']))
        count += self._reordered_privacy(str(row['privacy_can_publish']))
        count += self._reordered_address(str(row['internal_address']))
        count += self._reordered_address(str(row['real_address']))
        count += self._reordered_address(str(row['remote_address']))

        return count >= 2

    def _looks_good(self, row, has_latency):
        ''' Returns true if the row looks good after reordering '''

        # indirection table
        functions = {
                     'timestamp': self._reordered_timestamp,
                     'uuid': self._reordered_uuid,
                     'internal_address': self._reordered_address,
                     'real_address': self._reordered_address,
                     'remote_address': self._reordered_address,
                     'privacy_informed': self._reordered_privacy,
                     'privacy_can_collect': self._reordered_privacy,
                     'privacy_can_publish': self._reordered_privacy,
                     'connect_time': self._reordered_connect_time,
                     'latency': self._reordered_connect_time,
                     'upload_speed': self._reordered_speed,
                     'download_speed': self._reordered_speed,
                     'neubot_version': self._reordered_version,
                     'platform': self._reordered_platform,
                    }

        if not has_latency:
            del functions['latency']

        #
        # Note: the type of row[key] may not be the type we expect
        # because of rows reordering, so convert to string.
        #
        for key, function in functions.items():
            if function(str(row[key])):
                # Seen reordering
                return False

        # Looks good
        return True

    #   ___                     _   _
    #  / _ \ _ __  ___ _ _ __ _| |_(_)___ _ _  ___
    # | (_) | '_ \/ -_) '_/ _` |  _| / _ \ ' \(_-<
    #  \___/| .__/\___|_| \__,_|\__|_\___/_||_/__/
    #       |_|
    #
    # Build the list of operations (swappings) that we will
    # them perform later in a batch.
    #

    def build_operations(self, connection, table, operations):
        ''' Build operations for table '''

        good, fixed, nonfixed = 0, 0, 0

        if table == 'speedtest':
            has_latency = True
            swappings = self.speedtest_swappings
        elif table == 'bittorrent':
            has_latency = False
            swappings = self.bittorrent_swappings
        else:
            raise RuntimeError('migrate2: %s: invalid table name' % table)

        cursor = connection.cursor()
        cursor.execute('SELECT * FROM %s;' % table)
        for row in cursor:

            # Avoid consuming too much memory
            if len(operations) >= 4096:
                ncursor = connection.cursor()
                for operation in operations:
                    ncursor.execute(operation[0], operation[1])
                ncursor.close()
                del ncursor, operations[:]

            # Was reordered?
            if not self._seems_reordered(row):
                good = good + 1
                continue

            new_operations = []
            new_row = {}
            for left, right in swappings:
                value = row[left]

                #
                # Since we are pulling values from rows having the WRONG
                # type, we must cast them back to the EXPECTED type.
                # If we are unable to convert the type back to the type
                # we would have expected, we have made an error and we
                # should have not reordered the row, so undo.
                #
                try:
                    if value is not None:
                        if right in self.integers:
                            value = int(value)
                        elif right in self.floats:
                            value = float(value)
                        else:
                            value = str(value)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    nonfixed = nonfixed + 1
                    continue

                new_row[right] = value

                #
                # Prepare query
                # We safely print into the query string because `right`
                # comes from the swappings.
                #
                query = 'UPDATE %s SET %s=? WHERE id=?;' % (table, right)
                new_operations.append(( query, (value, row['id']) ))

            # Does it looks good now?
            if not self._looks_good(new_row, has_latency):

                #
                # I've seen this in the wild, in the period between
                # Neubot 0.4.5 and 0.4.6-rc2:
                #
                if new_row['privacy_can_publish'] is None:
                    new_row['privacy_can_publish'] = 0

                    if not self._looks_good(new_row, has_latency):
                        # This time really give up
                        nonfixed = nonfixed + 1
                        continue

                #
                # Very old Neubot versions have either None or ''
                # unique identifier, try to cope with those as well,
                # but be careful to keep original values.
                # NB: the intersection between this new case and
                # the above one SHOULD be empty.
                #
                elif new_row['uuid'] in (None, ''):
                    saved_uuid = new_row['uuid']
                    new_row['uuid'] = '71d22636-a584-441e-99ea-32c11ce073ef'

                    if not self._looks_good(new_row, has_latency):
                        # This time really give up
                        nonfixed = nonfixed + 1
                        continue

                    new_row['uuid'] = saved_uuid

                else:
                    nonfixed = nonfixed + 1
                    continue

            operations.extend(new_operations)
            fixed = fixed + 1

        return good, fixed, nonfixed

    @classmethod
    def migrate(cls, connection):
        ''' Migrate: 4.2 -> 4.3 '''

        try:
            logging.info('migrate2: fix reordering column bug of v4.2')

            instance = cls()
            operations = []

            for tbl in ('bittorrent', 'speedtest'):
                logging.info('migrate2: build operations for %s...', tbl)
                result = instance.build_operations(connection, tbl, operations)
                logging.info('migrate2: built operations for %s: %s',
                             tbl, str(result))

            cursor = connection.cursor()
            for operation in operations:
                cursor.execute(operation[0], operation[1])
            cursor.close()

        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            exc = asyncore.compact_traceback()
            logging.error('migrate2: cannot recover from reordering column '
                          'bug, please contact Neubot developers and report '
                          'this problem.')
            logging.error('migrate2: error details: %s', str(exc))

        logging.info('migrate2: from schema version 4.2 to 4.3')
        connection.execute('''UPDATE config SET value='4.3'
                              WHERE name='version';''')

        connection.commit()


# ===================
# Migrate: 4.3 -> 4.4
# ===================

def migrate_from_4_3_to_4_4(connection):
    ''' Migrate: 4.3 -> 4.4 '''

    logging.info('migrate2: from schema version 4.3 to 4.4...')

    connection.execute("ALTER TABLE speedtest ADD test_version INTEGER;")
    connection.execute("ALTER TABLE bittorrent ADD test_version INTEGER;")
    connection.execute('''UPDATE config SET value='4.4'
                              WHERE name='version';''')
    connection.commit()

    logging.info('migrate2: from schema version 4.3 to 4.4... done')


# ===================
# Migrate: 4.4 -> 4.5
# ===================

def migrate_from_4_4_to_4_5(connection):
    ''' Migrate: 4.4 -> 4.5 '''
    logging.info('migrate2: from schema version 4.4 to 4.5... in progress')
    connection.execute('''CREATE TABLE IF NOT EXISTS raw (
                            id INTEGER PRIMARY KEY, internal_address TEXT,
                            latency REAL, neubot_version TEXT,
                            timestamp INTEGER, connect_time REAL,
                            remote_address TEXT, download_speed REAL,
                            json_data TEXT, real_address TEXT,
                            uuid TEXT, platform TEXT);''')
    connection.execute('''UPDATE config SET value='4.5'
                              WHERE name='version';''')
    connection.commit()
    logging.info('migrate2: from schema version 4.4 to 4.5... complete')


# ====
# Main
# ====

MIGRATORS = {
    '4.2': MigrateFrom42To43.migrate,
    '4.3': migrate_from_4_3_to_4_4,
    '4.4': migrate_from_4_4_to_4_5,
}

def migrate(connection):
    ''' Migrate database '''

    logging.debug('migrate2: checking whether we need to migrate...')
    while True:

        cursor = connection.cursor()
        cursor.execute('SELECT value FROM config WHERE name="version";')
        version = cursor.fetchone()[0]

        if not version in MIGRATORS:
            logging.debug('migrate2: done')
            break

        migrator = MIGRATORS[version]
        migrator(connection)

def main(args):
    ''' main function '''

    arguments = args[1:]

    if not arguments:
        maxkey = max(MIGRATORS.keys())
        dest = MIGRATORS[maxkey].__doc__
        dest = dest[dest.index('->') + len('->'):].strip()
        sys.stdout.write('%s\n' % dest)
        sys.exit(0)

    for path in arguments:
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        migrate(connection)

if __name__ == '__main__':
    main(sys.argv)
