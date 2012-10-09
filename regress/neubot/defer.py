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


''' Regression test for neubot/defer.py '''

import logging
import sys
import unittest

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.defer import Deferred
from neubot.defer import Failure

def _call(function, argument, fake_logger=None):
    ''' Replace logging.warning with fake_logger, call function and
        then restore the original logger '''
    if fake_logger == None:
        fake_logger = logging.debug
    saved_func = logging.warning
    logging.warning = fake_logger
    try:
        function(argument)
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        raise
    finally:
        logging.warning = saved_func

def _replace_logging_warning(func):
    ''' Replace logging warning function with func '''
    ofunc = logging.warning
    logging.warning = func
    return ofunc

class Empty(unittest.TestCase):

    ''' Make sure an empty deferred behaves properly '''

    @staticmethod
    def test_callback():
        ''' Invoke callback() on empty deferred '''
        deferred = Deferred()
        deferred.callback(65537)

    @staticmethod
    def test_errback():
        ''' Invoke errback() on empty deferred '''
        deferred = Deferred()
        deferred.errback(65537)

class CallbackChain(unittest.TestCase):

    ''' Make sure the callback chain works '''

    counter = 0

    def test_callback_chain(self):
        ''' Make sure the callback chain works '''
        deferred = Deferred()
        deferred.add_callback(self._callback)
        deferred.add_callback(self._callback)
        deferred.add_callback(self._callback)
        deferred.callback(0)
        self.assertEqual(self.counter, 3)

    def _callback(self, result):
        ''' Function invoked as callback '''
        self.counter = result + 1
        return self.counter

class ErrbackChain(unittest.TestCase):

    ''' Make sure the errback chain works '''

    failure = Failure()
    counter = 0

    def test_errback_chain(self):
        ''' Make sure the errback chain works '''
        deferred = Deferred()
        deferred.add_errback(self._errback)
        deferred.add_errback(self._errback)
        deferred.add_errback(self._errback_last)
        deferred.errback(self.failure)
        self.assertEqual(self.counter, 3)

    def _errback(self, failure):
        ''' Function invoked as errback '''
        self.counter += 1
        self.assertEqual(failure, self.failure)
        return failure

    def _errback_last(self, failure):
        ''' Last errback function in the chain '''
        self.counter += 1
        self.assertEqual(failure, self.failure)

class ErrbackPrintWarning(unittest.TestCase):

    ''' Make sure default errback prints a warning message '''

    count = 0
    failure = Failure()

    def test_errback_default(self):
        ''' Make sure default errback prints a warning message '''
        deferred = Deferred()
        deferred.add_errback(self._errback)
        deferred.add_errback(self._errback)
        _call(deferred.errback, self.failure, self._logging_warning)
        self.assertTrue(self.count)

    @staticmethod
    def _errback(failure):
        ''' Function invoked as errback '''
        return failure

    def _logging_warning(self, *args):
        ''' Helper function to check whether logging.warning is invoked '''
        # Sum len of arguments to keep pylint quiet
        self.count += 1 + len(args)

class CallbackToErrback(unittest.TestCase):

    ''' Make sure we switch correctly from callback to errback '''

    count_callbacks = 0
    count_errbacks = 0

    def test_callback_to_errback(self):
        ''' Make sure we switch correctly from callback to errback '''
        deferred = Deferred()
        deferred.add_callback(self._callback)
        deferred.add_errback(self._errback)
        _call(deferred.callback, 65537)
        self.assertEqual(self.count_callbacks, 1)
        self.assertEqual(self.count_errbacks, 1)

    def _callback(self, result):
        ''' Function that is invoked as callback and fails '''
        self.count_callbacks += 1
        return result / 0

    def _errback(self, failure):
        ''' Function invoked as errback '''
        self.count_errbacks += 1
        self.assertEqual(failure.type, ZeroDivisionError)
        self.assertEqual(str(failure.value),
          'integer division or modulo by zero')
        return failure

class ErrbackToCallback(unittest.TestCase):

    ''' Make sure we switch correctly from errback to callback '''

    count_callbacks = 0
    count_errbacks = 0

    def test_callback_to_errback(self):
        ''' Make sure we switch correctly from errback to callback '''
        deferred = Deferred()
        deferred.add_callback(self._callback)
        deferred.add_errback(self._errback)
        deferred.add_callback(self._callback)
        _call(deferred.callback, 0)
        self.assertEqual(self.count_callbacks, 2)
        self.assertEqual(self.count_errbacks, 1)

    def _callback(self, result):
        ''' Function that is invoked as callback and fails '''
        self.count_callbacks += 1
        return 1 / result

    def _errback(self, failure):
        ''' Function invoked as errback '''
        self.count_errbacks += 1
        self.assertEqual(failure.type, ZeroDivisionError)
        self.assertEqual(str(failure.value),
          'integer division or modulo by zero')
        return 65537

class PingPong(unittest.TestCase):

    ''' Make sure we ping pong between callback and errback '''

    count_callbacks = 0
    count_errbacks = 0

    def test_deferred_ping_pong(self):
        ''' Make sure we ping pong between callback and errback '''
        deferred = Deferred()

        deferred.add_errback(self._errback)
        deferred.add_callback(self._callback)
        deferred.add_callback(self._callback)
        deferred.add_errback(self._errback)
        deferred.add_callback(self._callback)
        deferred.add_errback(self._errback)

        _call(deferred.callback, 0)

        self.assertEqual(self.count_callbacks, 2)
        self.assertEqual(self.count_errbacks, 2)

    def _callback(self, result):
        ''' Function invoked as callback '''
        self.count_callbacks += 1
        return 1 / result

    def _errback(self, failure):
        ''' Function invoked as errback '''
        self.count_errbacks += 1
        self.assertEqual(failure.type, ZeroDivisionError)
        self.assertEqual(str(failure.value),
          'integer division or modulo by zero')
        return 0

if __name__ == '__main__':
    unittest.main()
