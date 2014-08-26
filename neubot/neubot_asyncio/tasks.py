#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

from .futures import _Future

def _async(coro_or_future, **kwargs):
    # This implementation is very `create_connection()` specific
    if not isinstance(coro_or_future, _Future):
        raise RuntimeError("Invalid argument")
    return coro_or_future
