# neubot/defer.py

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

''' Simple deferred '''

import collections
import logging
import sys
import traceback

class Failure(object):
    ''' Represents a failure '''

    def __init__(self):
        self.type, self.value = sys.exc_info()[:2]
        self.trace = traceback.format_exc()

    def __str__(self):
        return self.trace

CALLBACK, ERRBACK = False, True  # match isfailure

class Deferred(object):
    ''' Simple deferred object '''

    def __init__(self):
        self.chain = collections.deque()

    def __len__(self):
        return len(self.chain)

    def add_callback(self, func):
        ''' Add a callback to the deferred '''
        self.chain.append((CALLBACK, func))

    def add_errback(self, func):
        ''' Add an errback to the deferred '''
        self.chain.append((ERRBACK, func))

    def callback_each_np(self, argument):
        ''' Pass argument to every function in the chain (non portable) '''
        while self.chain:
            func = self.chain.popleft()[1]
            try:
                func(argument)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.warning('defer: unhandled error\n%s', Failure())

    def callback(self, argument):
        ''' Run the callback/errback chain '''
        while self.chain:
            kind, func = self.chain.popleft()
            isfailure = isinstance(argument, Failure)
            if kind != isfailure:
                continue
            try:
                argument = func(argument)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                argument = Failure()
        if isinstance(argument, Failure):
            logging.warning('defer: unhandled error\n%s', argument)

    def errback(self, argument):
        ''' Run the callback/errback chain '''
        self.callback(argument)
