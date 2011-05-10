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

import sys

sys.path.insert(0, ".")

from neubot.blocks import RANDOMBLOCKS
from neubot.blocks import RandomFile
from neubot import utils

def main():
    assert(len(RANDOMBLOCKS.get_block()) == RANDOMBLOCKS.blocksiz)
    assert(RANDOMBLOCKS.get_block() != RANDOMBLOCKS.get_block())

    fp, total = RandomFile(RANDOMBLOCKS.blocksiz + 789), 0
    while True:
        block = fp.read(128)
        if not block:
            break
        total += len(block)
    assert(total == RANDOMBLOCKS.blocksiz + 789)

    fp = RandomFile(RANDOMBLOCKS.blocksiz + 789)
    assert(len(fp.read()) == RANDOMBLOCKS.blocksiz)
    assert(fp.tell() == 789)
    assert(len(fp.read()) == 789)
    fp.seek(7)

    begin, total = utils.ticks(), 0
    try:
        while True:
            total += len(RANDOMBLOCKS.get_block())
    except KeyboardInterrupt:
        print "Interrupt"

    print "Speed:", utils.speed_formatter(total/(utils.ticks() - begin))

if __name__ == "__main__":
    main()
