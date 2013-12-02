# neubot/poller.py

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
# pylint: disable=C0103
# Was: neubot/net/poller.py
# Python3-ready: yes
#

import sys
import os

from neubot.poller_libevent import PollerLibevent
from neubot.poller_libevent import PollableLibevent
from neubot.poller_neubot import PollerNeubot
from neubot.poller_neubot import PollableNeubot

if os.environ.get("NEUBOT_USE_LIBNEUBOT"):
    from neubot.poller_libneubot import PollableLibneubot
    from neubot.poller_libneubot import PollerLibneubot
    sys.stdout.write("neubot: poller engine: libneubot\n")
    POLLER = PollerLibneubot()
    Pollable = PollableLibneubot

elif os.environ.get("NEUBOT_USE_LIBEVENT"):
    sys.stdout.write("neubot: poller engine: libevent\n")
    POLLER = PollerLibevent()
    Pollable = PollableLibevent

else:
    sys.stdout.write("neubot: poller engine: neubot\n")
    POLLER = PollerNeubot()
    Pollable = PollableNeubot
