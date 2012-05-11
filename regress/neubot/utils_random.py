#!/usr/bin/env python

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

''' Unit test for neubot/utils_random.py '''

import sys

sys.path.insert(0, '.')

from neubot import utils

BEFORE = utils.ticks()
from neubot.utils_random import RANDOMBLOCKS
from neubot.utils_random import RandomBody
ELAPSED = utils.ticks() - BEFORE
print('Time to import: %s' % (utils.time_formatter(ELAPSED)))

def main():

    ''' Unit test for neubot/utils_random.py '''

    assert(len(RANDOMBLOCKS.get_block()) == RANDOMBLOCKS.blocksiz)
    assert(RANDOMBLOCKS.get_block() != RANDOMBLOCKS.get_block())

    filep, total = RandomBody(RANDOMBLOCKS.blocksiz + 789), 0
    while True:
        block = filep.read(128)
        if not block:
            break
        total += len(block)
    assert(total == RANDOMBLOCKS.blocksiz + 789)

    filep = RandomBody(RANDOMBLOCKS.blocksiz + 789)
    assert(len(filep.read()) == RANDOMBLOCKS.blocksiz)
    assert(filep.tell() == 789)
    assert(len(filep.read()) == 789)
    filep.seek(7)

    begin, total = utils.ticks(), 0
    while total < 1073741824:
        total += len(RANDOMBLOCKS.get_block())
    elapsed = utils.ticks() - begin

    print('Elapsed: %s' % utils.time_formatter(elapsed))
    print('Speed: %s' % utils.speed_formatter(total/elapsed))

if __name__ == "__main__":
    main()
