#!/usr/bin/env python

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

''' Regression tests for neubot/privacy.py '''

#
# Disable annoying PyLint warning pointing out that TestCase
# defines too many methods.
#
# pylint: disable=R0904
#

import unittest
import sqlite3
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.config import CONFIG
from neubot.config import ConfigError
from neubot.database import table_config
from neubot import privacy

class TestPrivacyCountValid(unittest.TestCase):

    ''' Regression tests for neubot.privacy.count_valid() '''

    def test_empty_cases(self):
        ''' Make sure it returns 0 when there is nothing interesting '''

        # Nothing in input
        self.assertEqual(0, privacy.count_valid(
          {}, ""))

        # Wrong prefix
        self.assertEqual(0, privacy.count_valid(
          {'privacy.informed': 1}, "privacy_"))

    def test_good_cases(self):
        ''' Make sure it correctly counts the number of valid settings '''

        for prefix in ('privacy.', 'privacy_'):
            for trueval in (1, '1', 'true', 'on', 'yes'):

                self.assertEqual(1, privacy.count_valid(
                  {'%sinformed' % prefix: trueval},
                  prefix))

                self.assertEqual(1, privacy.count_valid(
                  {'%scan_collect' % prefix: trueval},
                  prefix))

                self.assertEqual(1, privacy.count_valid(
                  {'%scan_publish' % prefix: trueval},
                  prefix))

                self.assertEqual(3, privacy.count_valid(
                  {'%sinformed' % prefix: trueval,
                   '%scan_collect' % prefix: trueval,
                   '%scan_publish' % prefix: trueval},
                  prefix))

    def test_bad(self):
        ''' Make sure it returns -1 when settings are bad '''

        # False value
        self.assertEqual(-1, privacy.count_valid(
          {'privacy.informed': 0}, "privacy."))
        self.assertEqual(-1, privacy.count_valid(
          {'privacy.can_collect': 0}, "privacy."))
        self.assertEqual(-1, privacy.count_valid(
          {'privacy.can_publish': 0}, "privacy."))

        # Not all are True
        self.assertEqual(-1, privacy.count_valid(
          {'privacy.informed': 0,
           'privacy.can_collect': 0,
           'privacy.can_publish': 0},
          "privacy."))
        self.assertEqual(-1, privacy.count_valid(
          {'privacy.informed': 0,
           'privacy.can_collect': 0,
           'privacy.can_publish': 1},
          "privacy."))
        self.assertEqual(-1, privacy.count_valid(
          {'privacy.informed': 0,
           'privacy.can_collect': 1,
           'privacy.can_publish': 0},
          "privacy."))
        self.assertEqual(-1, privacy.count_valid(
          {'privacy.informed': 0,
           'privacy.can_collect': 1,
           'privacy.can_publish': 1},
          "privacy."))
        self.assertEqual(-1, privacy.count_valid(
          {'privacy.informed': 1,
           'privacy.can_collect': 0,
           'privacy.can_publish': 0},
          "privacy."))
        self.assertEqual(-1, privacy.count_valid(
          {'privacy.informed': 1,
           'privacy.can_collect': 0,
           'privacy.can_publish': 1},
          "privacy."))
        self.assertEqual(-1, privacy.count_valid(
          {'privacy.informed': 1,
           'privacy.can_collect': 1,
           'privacy.can_publish': 0},
          "privacy."))

class TestPrivacyCheck(unittest.TestCase):

    ''' Regression tests for neubot.privacy.check() '''

    @staticmethod
    def test_check_success():
        ''' Make sure check() accepts valid dictionaries '''

        privacy.check({'privacy.informed': 1})
        privacy.check({'privacy_informed': 1},
                      prefix='privacy_')
        privacy.check({'privacy.informed': 1,
                       'privacy.can_collect': 1,
                       'privacy.can_publish': 1},
                      check_all=True)

    def test_check_failure(self):
        ''' Make sure check() fails on invalid dictionaries '''

        self.assertRaises(ConfigError, privacy.check,
                          {'privacy.informed': 0})
        self.assertRaises(ConfigError, privacy.check,
                          {'privacy.informed': 1,
                           'privacy.can_collect': 0,
                           'privacy.can_publish': 1})

    def test_check_failure_all(self):
        ''' Make sure check() fails when not all settings are present '''

        self.assertRaises(ConfigError, privacy.check,
                          {'privacy.informed': 1,
                           'privacy.can_collect': 1},
                          check_all=True)

class TestCollectAllowed(unittest.TestCase):

    ''' Regression tests for neubot.privacy.collect_allowed() '''

    def test_success(self):
        ''' Make sure collect_allowed() returns True on valid input '''
        self.assertTrue(privacy.collect_allowed(
          {'privacy_informed': 1,
           'privacy_can_collect': 1,
           'privacy_can_publish': 0}))
        self.assertTrue(privacy.collect_allowed(
          {'privacy_informed': 1,
           'privacy_can_collect': 1,
           'privacy_can_publish': 1}))

    def test_failure(self):
        ''' Make sure collect_allowed() returns False on bad input '''
        self.assertFalse(privacy.collect_allowed(
          {'privacy_informed': 0,
           'privacy_can_collect': 0,
           'privacy_can_publish': 0}))
        self.assertFalse(privacy.collect_allowed(
          {'privacy_informed': 0,
           'privacy_can_collect': 0,
           'privacy_can_publish': 1}))
        self.assertFalse(privacy.collect_allowed(
          {'privacy_informed': 0,
           'privacy_can_collect': 1,
           'privacy_can_publish': 0}))
        self.assertFalse(privacy.collect_allowed(
          {'privacy_informed': 0,
           'privacy_can_collect': 1,
           'privacy_can_publish': 1}))
        self.assertFalse(privacy.collect_allowed(
          {'privacy_informed': 1,
           'privacy_can_collect': 0,
           'privacy_can_publish': 0}))
        self.assertFalse(privacy.collect_allowed(
          {'privacy_informed': 1,
           'privacy_can_collect': 0,
           'privacy_can_publish': 1}))

class TestAllowedToRun(unittest.TestCase):

    ''' Regression tests for neubot.privacy.allowed_to_run() '''

    def test_success(self):
        ''' Make sure allowed_to_run() returns True on valid CONFIG '''
        CONFIG.merge_kv(('privacy.informed', 1))
        CONFIG.merge_kv(('privacy.can_collect', 1))
        CONFIG.merge_kv(('privacy.can_publish', 1))
        self.assertTrue(privacy.allowed_to_run())

    def test_failure(self):
        ''' Make sure collect_allowed() returns False on bad input '''
        CONFIG.merge_kv(('privacy.informed', 1))
        CONFIG.merge_kv(('privacy.can_collect', 1))
        CONFIG.merge_kv(('privacy.can_publish', 0))
        self.assertFalse(privacy.allowed_to_run())

class TestPrintPolicy(unittest.TestCase):

    ''' Regression tests for neubot.privacy.print_policy() '''

    def test_works(self):
        ''' Make sure print_policy() works '''
        self.assertEqual(privacy.print_policy(), 0)

class TestTestSettings(unittest.TestCase):

    ''' Regression tests for neubot.privacy.test_settings() '''

    def test_success(self):
        ''' Make sure test_settings() returns 0 for a valid database '''

        connection = sqlite3.connect(':memory:')
        table_config.create(connection)
        table_config.update(connection, {
                                         'privacy.informed': 1,
                                         'privacy.can_collect': 1,
                                         'privacy.can_publish': 1
                                        }.iteritems())

        self.assertEqual(privacy.test_settings(connection), 0)

    def test_failure(self):
        ''' Make sure test_settings() returns 1 for a bad database '''

        connection = sqlite3.connect(':memory:')
        table_config.create(connection)
        table_config.update(connection, {
                                         'privacy.informed': 1,
                                         'privacy.can_collect': 1,
                                         'privacy.can_publish': 0
                                        }.iteritems())

        self.assertEqual(privacy.test_settings(connection), 1)

    def test_legacy(self):
        ''' Make sure test_settings() returns 1 for a legacy database '''

        #
        # This case should not happen, still I want to be sure
        # an error would be reported in this case.
        #

        connection = sqlite3.connect(':memory:')
        table_config.create(connection)
        table_config.update(connection, {
                                         'privacy.informed': 1,
                                         'privacy.can_collect': 1,
                                         'privacy.can_publish': 1
                                        }.iteritems())

        # Go back to version 4.1 of the database
        connection.execute(''' UPDATE config SET name="privacy.can_share"
                               WHERE name="privacy.can_publish" ''')

        self.assertEqual(privacy.test_settings(connection), 1)

class TestUpdateSettings(unittest.TestCase):

    ''' Regression tests for neubot.privacy.update_settings() '''

    def test_works(self):
        ''' Make sure that update_settings() works '''

        connection = sqlite3.connect(':memory:')
        table_config.create(connection)

        privacy.update_settings(connection, {
                                             'privacy.informed': 4,
                                             'privacy.can_collect': 5,
                                             'privacy.can_publish': 6,
                                             'foo': 'bar',
                                            })

        content = table_config.dictionarize(connection)

        # Make sure foo: bar was not added
        self.assertEqual(sorted(content.keys()), sorted([
                                                         'uuid', 'version',
                                                         'privacy.informed',
                                                         'privacy.can_collect',
                                                         'privacy.can_publish'
                                                        ]))

        # Make sure settings were added correctly
        self.assertEqual(content['privacy.informed'], '4')
        self.assertEqual(content['privacy.can_collect'], '5')
        self.assertEqual(content['privacy.can_publish'], '6')

class TestPrintSettings(unittest.TestCase):

    ''' Regression tests for neubot.privacy.print_settings() '''

    def test_works(self):
        ''' Make sure print_settings() works '''

        connection = sqlite3.connect(':memory:')
        table_config.create(connection)

        privacy.update_settings(connection, {
                                             'privacy.informed': 4,
                                             'privacy.can_collect': 5,
                                             'privacy.can_publish': 6,
                                            })

        self.assertEqual(privacy.print_settings(connection,
          ':memory:'), 0)

if __name__ == '__main__':
    unittest.main()
