# neubot/blocks.py

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

import collections
import random

#
# This class generates random fixed-size blocks by rotating
# and merging a number of initial words counting up to the
# expected length of the block.  The rotation does not generate
# much entropy, but this method is fast and much better than
# using "AAAA...A".
# Note that the idea of rotating the deque is taken from a
# blog post by Jesse Noller <http://bit.ly/irj8je>.
#
class RandomBlocks(object):
    def __init__(self, blocksiz=262144):
        self.words = collections.deque()
        self.blocksiz = blocksiz
        while blocksiz > 0:
            wordlen = random.randint(1, min(16, blocksiz))
            blocksiz -= wordlen
            word = []
            for _ in range(wordlen):
                word.append(chr(random.randint(32, 126)))
            self.words.append("".join(word))

    def get_block(self):
        self.words.rotate(random.randrange(0, 16))
        return "".join(self.words)

RANDOMBLOCKS = RandomBlocks()

#
# This class implements a minimal file-like interface and
# employs the random number generator to create the content
# returned by its read() method.
#
class RandomBody(object):
    def __init__(self, total):
        self.total = int(total)

    def read(self, n=None):
        if not n:
            n = self.total
        amt = min(self.total, min(n, RANDOMBLOCKS.blocksiz))
        if amt:
            self.total -= amt
            return RANDOMBLOCKS.get_block()[:amt]
        else:
            return ""

    def seek(self, offset=0, whence=0):
        pass

    def tell(self):
        return self.total
