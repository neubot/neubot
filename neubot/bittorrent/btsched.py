# neubot/bittorrent/btsched.py

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

''' BitTorrent requests scheduler '''

import random

#
# Given our bitfield and peer's bitfield, this generator
# returns all the indexes of the pieces we're missing and
# that the peer has.
# Note that we walk our bitmap in random order so the list
# of requested pieces is not monotonic.
#
def sched_idx(bitfield, peer_bitfield):

    ''' Schedules the next index '''

    assert(len(bitfield.bits) == len(peer_bitfield.bits))
    vector = range(len(bitfield.bits))
    random.shuffle(vector)
    for index in vector:
        if not bitfield.bits[index] and peer_bitfield.bits[index]:
            idx = index << 3
            kvec = range(8)
            random.shuffle(kvec)
            for k in kvec:
                yield idx + k

#
# Given our bitfield, the peer's bitfield, the number of bytes
# we want to transfer and the length of the piece, this generator
# returns the vector of (index, begin, length) that we should
# request to our peer at any given time.
# Note that there is an initial burst whose goal is to try to
# fill the pipeline between us and the peer, in order to emulate
# a continuous transfer of a huge file.
#
def sched_req(bitfield, peer_bitfield, targetbytes, piecelen, blocklen):

    ''' Schedules the next list of pieces we must request '''

    # Adapt initial burst to the channel
    burstlen = int(targetbytes/3)
    total = burstlen + targetbytes

    # Create next-piece-index generator
    idx = sched_idx(bitfield, peer_bitfield)

    # Return first burst, then single requests
    cnt = 0
    burst = []
    for req in _sched_piece(idx, total, piecelen, blocklen):
        if cnt < burstlen:
            burst.append(req)
            cnt += req[2]
            if cnt >= burstlen:
                yield burst
        else:
            yield [req]

#
# Generator that returns BitTorrent REQUESTs parameters
# to request up to `total` bytes.  Each piece has size
# `piecelen`, each block has size `blocklen` and `idx` is
# an iterator that returns the index of the next piece
# we want to download.
#
def _sched_piece(idx, total, piecelen, blocklen):

    ''' Schedules the next piece we should request '''

    if blocklen > piecelen:
        raise RuntimeError('Received invalid parameters')

    # Piece info
    cur_left, cur_idx, cur_offset = 0, 0, 0

    while total > 0:

        # Piece exhausted?  Pick next one
        if cur_left == 0:
            cur_idx = idx.next()
            cur_left = piecelen
            cur_offset = 0

        # Request block from piece
        amt = min(total, cur_left, blocklen)

        # Feed the caller
        yield (cur_idx, cur_offset, amt)

        # Accounting
        cur_left -= amt
        cur_offset += amt
        total -= amt
