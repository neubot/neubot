#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

from ._futures import _FutureImpl

def _async(coro_or_future, **kwargs):
    # This implementation is very `create_connection()` specific
    if not isinstance(coro_or_future, _FutureImpl):
        raise RuntimeError("Invalid argument")
    return coro_or_future
