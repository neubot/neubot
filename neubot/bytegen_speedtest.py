# neubot/bytegen_speedtest.py

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

''' Generates bytes for the speedtest test '''

import getopt
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.utils_random import RANDOMBLOCKS
from neubot import utils

PIECE_LEN = 262144

class BytegenSpeedtest(object):
    ''' Bytes generator for speedtest '''

    def __init__(self, seconds, piece_len=PIECE_LEN):
        ''' Initializer '''
        self.seconds = seconds
        self.ticks = utils.ticks()
        self.closed = False
        self.piece_len = piece_len

    def read(self, count=sys.maxint):
        ''' Read count bytes '''

        if self.closed:
            return ''
        if count < self.piece_len:
            raise RuntimeError('Invalid count')

        diff = utils.ticks() - self.ticks
        if diff < self.seconds:
            data = RANDOMBLOCKS.get_block()[:self.piece_len]
            length = '%x\r\n' % self.piece_len
            vector = [ length, data, '\r\n' ]
        else:
            vector = [ '0\r\n', '\r\n' ]
            self.closed = True

        return ''.join(vector)

    def close(self):
        ''' Close  '''
        self.closed = True

def main(args):
    ''' Main() function '''

    try:
        options, arguments = getopt.getopt(args[1:], 't:')
    except getopt.error:
        sys.exit('usage: neubot bytegen_speedtest [-t seconds]')
    if arguments:
        sys.exit('usage: neubot bytegen_speedtest [-t seconds]')

    seconds = 5.0
    for name, value in options:
        if name == '-t':
            seconds = float(value)

    bytegen = BytegenSpeedtest(seconds)
    while True:
        data = bytegen.read()
        if not data:
            break
        sys.stdout.write(data)

if __name__ == '__main__':
    main(sys.argv)
