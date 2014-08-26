#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

from .futures import _CancelledError
from .futures import _FutureImpl
from .futures import _InvalidStateError
from ._globals import _get_event_loop

#
# pylint: disable = import-error
# pylint: disable = invalid-name
# pylint: disable = unused-import
# pylint: disable = too-few-public-methods
#

try:
    from asyncio import CancelledError
    from asyncio import Future
    from asyncio import InvalidStateError

except ImportError:
    class CancelledError(_CancelledError):
        pass

    class Future(_FutureImpl):
        def __init__(self, evloop=None):
            if not evloop:
                evloop = _get_event_loop()
            _FutureImpl.__init__(self, evloop)

    class InvalidStateError(_InvalidStateError):
        pass
