# neubot/poller_interface.py

#
# Copyright (c) 2010, 2012-2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>.
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
# Adapted-from: neubot/pollable.py
# Python3-ready: yes
# pylint: disable=C0111
#

class PollableInterface(object):

    def __init__(self, poller):
        pass

    def attach(self, filenum):
        pass

    def detach(self):
        pass

    def fileno(self):
        pass

    def set_readable(self):
        pass

    def unset_readable(self):
        pass

    def handle_read(self):
        pass

    def set_writable(self):
        pass

    def unset_writable(self):
        pass

    def handle_write(self):
        pass

    def set_timeout(self, delta):
        pass

    def clear_timeout(self):
        pass

    def handle_periodic(self):
        pass

    def close(self):
        pass

    def handle_close(self):
        pass

class PollerInterface(object):

    def __init__(self):
        pass

    def sched(self, delta, function, argument):
        pass

    def loop(self):
        pass

    def break_loop(self):
        pass
