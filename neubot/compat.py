# neubot/compat.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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
# We want to be compatible with Python2.5, where it's not
# possible to pass deque() the maximum deque length.
#

def deque_append(queue, maxlen, element):
    if len(queue) > maxlen:
        queue.popleft()
    queue.append(element)

def deque_appendleft(queue, maxlen, element):
    if len(queue) > maxlen:
        queue.pop()
    queue.appendleft(element)
