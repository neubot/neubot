# neubot/times.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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

"""
neubot/times.py
'''''''''''''''

The various definitions of time available in Neubot.

timestamp()
  Returns an integer representing the number of seconds elapsed
  since the EPOCH in UTC.

ticks()
  Returns a real representing the most precise clock available
  on the current platform.  Note that, depending on the platform,
  the returned value MIGHT NOT be a timestamp.  So, you MUST
  use this clock to calculate the time elapsed between two events
  ONLY.

T()
  Returns the opaque time, i.e. the time used to identify
  events by the web user interface.  This is an integer, and
  is calculated as follows: ``int(10^6 * ticks())``.  So,
  the same caveat regarding ticks() also applies to this
  function.
"""

import os
import time
import sys

timestamp = lambda: int(time.time())

if os.name == 'nt':
    ticks = time.clock
elif os.name == 'posix':
    ticks = time.time
else:
    raise ImportError("Please, provide a definition of ticks()")

T = lambda: int(1000000 * ticks())

if __name__ == "__main__":
    sys.stdout.write("OS          : %s\n" % os.name)
    sys.stdout.write("timestamp() : %d\n" % timestamp())
    sys.stdout.write("ticks()     : %f\n" % ticks())
    sys.stdout.write("T()         : %d\n" % T())
