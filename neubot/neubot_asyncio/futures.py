#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

import logging

class _InvalidStateError(Exception):
    pass

class _CancelledError(Exception):
    pass

class _Future(object):

    def __init__(self, **kwargs):
        evloop = kwargs.get("loop")
        self._callbacks = []
        self._is_cancelled = False
        self._raised_exception = None
        self._evloop = evloop
        self._result_obj = None
        self._has_valid_result = False

    def _run_callback_safe(self, callback):
        try:
            callback(self)
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception:
            logging.warning("future: callback error", exc_info=1)

    def _future_is_done(self):
        for callback in self._callbacks:
            self._run_callback_safe(callback)

    def cancel(self):
        if self.done():
            return True
        self._is_cancelled = True
        self._evloop.call_soon(self._future_is_done)
        return False

    def cancelled(self):
        return self._is_cancelled

    def done(self):
        return (self._is_cancelled or self._has_valid_result
                or self._raised_exception)

    #
    # Pylint is confused by _raised_exception initially being None.
    # pylint: disable = raising-bad-type
    #

    def result(self):
        if self._is_cancelled:
            raise _CancelledError()
        if self._has_valid_result:
            return self._result_obj
        if self._raised_exception:
            raise self._raised_exception
        raise _InvalidStateError()

    #
    # Re-enable the above error
    # pylint: enable = raising-bad-type
    #

    def exception(self):
        if self._is_cancelled:
            raise _CancelledError()
        if self._raised_exception:
            return self._raised_exception
        if self._has_valid_result:
            return None
        raise _InvalidStateError()

    def add_done_callback(self, callback):
        if self.done():
            self._evloop.call_soon(self._run_callback_safe, callback)
            return
        self._callbacks.append(callback)

    def remove_done_callback(self, callback):
        count = self._callbacks.count(callback)
        for _ in range(count):
            self._callbacks.remove(callback)
        return count

    def set_result(self, result):
        if self.done():
            raise _InvalidStateError()
        self._result_obj = result
        self._has_valid_result = True
        self._evloop.call_soon(self._future_is_done)

    def set_exception(self, exception):
        if self.done():
            raise _InvalidStateError()
        self._raised_exception = exception
        self._evloop.call_soon(self._future_is_done)
