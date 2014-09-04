#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

from ._eventloop import _get_event_loop
from .futures import _Future

def _wait_for(internal, timeout, **kwargs):
    """ Wait for the `internal` future to complete within `timeout'
        seconds, then force `internal` to fail """

    loop = kwargs.get("loop")
    if not loop:
        loop = _get_event_loop()

    def timeout_expired():
        internal.set_exception(RuntimeError("Timeout expired"))

    handle = loop.call_later(timeout, timeout_expired)
    external = _Future(loop=loop)

    def on_done(fut):
        handle.cancel()  # Delete pending timeout
        if fut.cancelled():
            external.cancel()
        elif fut.exception():
            external.set_exception(fut.exception())
        else:
            external.set_result(fut.result())

    internal.add_done_callback(on_done)
    return external

def _async(coro_or_future, **kwargs):
    # This implementation is very `create_connection()` specific
    if not isinstance(coro_or_future, _Future):
        raise RuntimeError("Invalid argument")
    return coro_or_future
