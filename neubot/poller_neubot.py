# neubot/poller_neubot.py

#
# Copyright (c) 2010, 2012-2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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

''' Dispatch read, write, periodic and other events '''

#
# Was: neubot/net/poller.py
# Adapted-from: neubot/poller.py
# Python3-ready: yes
#

import logging
import errno
import select
import sched
import sys

from neubot.poller_interface import PollableInterface
from neubot.poller_interface import PollerInterface
from neubot.utils import ticks
from neubot.utils import timestamp

#
# Number of seconds between each check for timed-out
# I/O operations.
#
CHECK_TIMEOUT = 10

class PollableNeubot(PollableInterface):

    # TODO: set a default timeout of 300 seconds

    def __init__(self, poller):
        PollableInterface.__init__(self, poller)
        self.poller = poller
        self.filenum = -1
        self.timeo = -1

    def attach(self, filenum):
        self.filenum = filenum

    def detach(self):
        if self.filenum < 0:
            return
        self.poller.unset_readable_(self)
        self.poller.unset_writable_(self)
        self.filenum = -1

    def fileno(self):
        return self.filenum

    def set_readable(self):
        self.poller.set_readable_(self)

    def unset_readable(self):
        self.poller.unset_readable_(self)

    def set_writable(self):
        self.poller.set_writable_(self)

    def unset_writable(self):
        self.poller.unset_writable_(self)

    def set_timeout(self, delta):
        self.timeo = ticks() + delta

    def clear_timeout(self):
        self.timeo = -1

    def handle_periodic(self):
        if self.timeo >= 0 and ticks() > self.timeo:
            logging.warning("poller_libevent: Watchdog timeout")
            self.close()

    def close(self):
        self.detach()
        self.handle_close()

    def handle_close(self):
        pass

class PollerNeubot(sched.scheduler, PollerInterface):

    ''' Dispatch read, write, periodic and other events '''

    #
    # We always keep the check_timeout_() event registered
    # so the scheduler is alive forever.
    # We register self._poll() as the delay function and
    # in that function we either invoke select() or we
    # sleep for the requested amount of time.
    #

    def __init__(self):
        ''' Initialize '''
        sched.scheduler.__init__(self, ticks, self._poll)
        PollerInterface.__init__(self)
        self.select_timeout = 1
        self.again = True
        self.readset = {}
        self.writeset = {}
        self.check_timeout_()

    def sched(self, delta, func, *args):  # FIXME
        ''' Schedule task '''
        #logging.debug('poller: sched: %s, %s, %s', delta, func, args)
        self.enter(delta, 0, self._run_task, (func, args))
        return timestamp() + delta

    @staticmethod
    def _run_task(func, args):
        ''' Safely run task '''
        #logging.debug('poller: run_task: %s, %s', func, args)
        try:
            if args:
                func(args)
            else:
                func()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.error('poller: run_task() failed', exc_info=1)

    def set_readable_(self, stream):
        ''' Monitor for readability '''
        self.readset[stream.fileno()] = stream

    def set_writable_(self, stream):
        ''' Monitor for writability '''
        self.writeset[stream.fileno()] = stream

    def unset_readable_(self, stream):
        ''' Stop monitoring for readability '''
        fileno = stream.fileno()
        if fileno in self.readset:
            del self.readset[fileno]

    def unset_writable_(self, stream):
        ''' Stop monitoring for writability '''
        fileno = stream.fileno()
        if fileno in self.writeset:
            del self.writeset[fileno]

    def close_(self, stream):
        ''' Safely close a stream '''
        try:
            stream.close()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.error('poller: handle_close() failed', exc_info=1)

    #
    # We are very careful when accessing readset and writeset because
    # it's possible that the fileno makes reference to a stream that
    # does not exist anymore.  Consider the following example: There is
    # a stream that is both readable and writable, and so its fileno
    # is both in res[0] and res[1].  But, when we invoke the stream's
    # readable() callback there is a protocol violation and so the
    # high-level code invokes close(), and the stream is closed, and
    # hence removed from readset and writeset.  And then the stream
    # does not exist anymore, but its fileno still is in res[1].
    #

    def _call_handle_read(self, fileno):
        ''' Safely dispatch read event '''
        if fileno in self.readset:
            stream = self.readset[fileno]
            try:
                stream.handle_read()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.error('poller: handle_read() failed', exc_info=1)
                self.close_(stream)

    def _call_handle_write(self, fileno):
        ''' Safely dispatch write event '''
        if fileno in self.writeset:
            stream = self.writeset[fileno]
            try:
                stream.handle_write()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.error('poller: handle_write() failed', exc_info=1)
                self.close_(stream)

    def break_loop(self):
        ''' Break out of poller loop '''
        self.again = False

    def loop(self):
        ''' Poller loop '''
        while True:
            try:
                self.run()
            except (SystemExit, select.error):
                raise
            except KeyboardInterrupt:
                break  # overriden semantic: break out of poller loop NOW
            except:
                logging.error('poller: unhandled exception', exc_info=1)

    def _poll(self, timeout):
        ''' Poll for readability and writability '''

        # Immediately break out of the loop if requested to do so
        if not self.again:
            raise KeyboardInterrupt('poller: self.again is false')

        # Monitor streams readability/writability
        elif self.readset or self.writeset:

            # Get list of readable/writable streams
            try:
                res = select.select(list(self.readset.keys()),
                                    list(self.writeset.keys()),
                                    [], timeout)
            except select.error:
                code = sys.exc_info()[1][0]
                if code != errno.EINTR:
                    logging.error('poller: select() failed', exc_info=1)
                    raise

                else:
                    # Take care of EINTR
                    return

            # No error?  Fire readable and writable events
            for fileno in res[0]:
                self._call_handle_read(fileno)
            for fileno in res[1]:
                self._call_handle_write(fileno)

        # No I/O pending?  Break out of the loop.
        else:
            raise KeyboardInterrupt('poller: no I/O pending')

    def check_timeout_(self):
        ''' Dispatch the periodic event '''

        self.sched(CHECK_TIMEOUT, self.check_timeout_)
        if self.readset or self.writeset:

            streams = set()
            streams.update(list(self.readset.values()))
            streams.update(list(self.writeset.values()))

            for stream in streams:
                stream.handle_periodic()

    def snap(self, data):  # FIXME
        ''' Take a snapshot of poller state '''
        data['poller'] = { "readset": self.readset, "writeset": self.writeset }
        if hasattr(self, 'queue'):
            data['poller']['queue'] = self.queue
