# neubot/utils_random.py

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

''' Generate random data blocks for the tests '''

#
# This code is inspired by code published on the blog
# of Jesse Noller <http://bit.ly/irj8je>.
#

import collections
import os.path
import random

#
# Must use WWWDIR because Python modules are not
# reachable with Windows.  They are stored into
# library.zip.
#
from neubot import utils_hier

# Maximum depth
MAXDEPTH = 16

# Size of a block
BLOCKSIZE = 262144

def listdir(curdir, vector, depth):

    ''' Make a list of all the files in a given directory
        up to a certain depth '''

    if depth > MAXDEPTH:
        return

    for entry in os.listdir(curdir):
        entry = os.path.join(curdir, entry)
        if os.path.isdir(entry):
            listdir(entry, vector, depth + 1)
        elif os.path.isfile(entry):
            vector.append(entry)

def create_base_block(length):

    ''' Create a base block of length @length '''

    base_block = collections.deque()

    files = []
    listdir(utils_hier.WWWDIR, files, 0)
    random.shuffle(files)

    for fpath in files:
        fileptr = open(fpath, 'rb')
        content = fileptr.read()
        words = content.split()

        for word in words:
            amount = min(len(word), length)
            word = word[:amount]
            wordlist = list(word)
            random.shuffle(wordlist)

            base_block.append(''.join(wordlist))
            length -= amount
            if length <= 0:
                break

        if length <= 0:
            break

    return base_block

def block_generator(size):

    ''' Generator that returns blocks '''

    block = create_base_block(size)
    while True:
        block.rotate(random.randrange(4, 16))
        yield ''.join(block)

class RandomBlocks(object):

    ''' Generate blocks randomly shuffling a base block '''

    def __init__(self, size=BLOCKSIZE):
        ''' Initialize random blocks generator '''
        self._generator = block_generator(size)
        self.blocksiz = size

    def reinit(self):
        ''' Reinitialize the generator '''
        self._generator = block_generator(self.blocksiz)

    def get_block(self):
        ''' Return a block of data '''
        return self._generator.next()

RANDOMBLOCKS = RandomBlocks()

#
# XXX Create and discard the first block at the very
# beginning, so we are sure that we can fetch all the
# needed files in the common case, i.e. when we
# startup as root.
#
RANDOMBLOCKS.get_block()

class RandomBody(object):

    '''
     This class implements a minimal file-like interface and
     employs the random number generator to create the content
     returned by its read() method.
    '''

    def __init__(self, total):
        ''' Initialize random body object '''
        self.total = int(total)

    def read(self, want=None):
        ''' Read up to @want bytes '''
        if not want:
            want = self.total
        amt = min(self.total, min(want, RANDOMBLOCKS.blocksiz))
        if amt:
            self.total -= amt
            return RANDOMBLOCKS.get_block()[:amt]
        else:
            return ''

    def seek(self, offset=0, whence=0):
        ''' Seek stub '''

    def tell(self):
        ''' Tell the amounts of bytes left '''
        return self.total
