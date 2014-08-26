#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

try:
    from asyncio import Protocol
    from asyncio import Transport
    from asyncio import async
    from asyncio import get_event_loop

except ImportError:
    from .protocols import _Protocol as Protocol
    from .transports import _Transport as Transport
    from .tasks import _async as async
    from ._globals import _get_event_loop as get_event_loop
