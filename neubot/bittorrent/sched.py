# neubot/bittorrent/sched.py

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

import random

#
# Given our bitfield and peer's bitfield, this generator
# returns all the indexes of the pieces we're missing and
# that the peer has.
# Note that we walk our bitmap in random order so the list
# of requested pieces is not monotonic.
#
def sched_idx(bitfield, peer_bitfield):
    assert(len(bitfield.bits) == len(peer_bitfield.bits))
    vector = range(len(bitfield.bits))
    random.shuffle(vector)
    for index in vector:
        if not bitfield.bits[index] and peer_bitfield.bits[index]:
            idx = index << 3
            for k in range(8):
                yield idx + k

#
# Given our bitfield, the peer's bitfield, the number of bytes
# we want to transfer, the length of the piece, and the amount of
# bytes we want to keep in the pipeline between us and the peer,
# this generator returns a vector of (index, begin, length) we
# should request to our peer at any given time.
#
def sched_req(bitfield, peer_bitfield, targetbytes, piecelen, pipeline):
    idx = sched_idx(bitfield, peer_bitfield)
    npieces = targetbytes // piecelen + 1
    npiecespipe = pipeline // piecelen + 1
    if npieces < npiecespipe:
        npieces = npiecespipe + 1
    burst = []
    for _ in range(min(npieces, npiecespipe)):
        burst.append((next(idx), 0, piecelen))
    yield burst
    npieces -= min(npieces, npiecespipe)
    for _ in range(npieces):
        yield [(next(idx), 0, piecelen)]
