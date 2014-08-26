#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

from ._eventloop import _EventLoop

_EVENT_LOOP = _EventLoop()

def _get_event_loop():
    return _EVENT_LOOP
