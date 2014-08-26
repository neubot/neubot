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
        self.callbacks = []
        self.is_cancelled = False
        self.raised_exception = None
        self.evloop = evloop
        self.result_obj = None
        self.has_valid_result = False

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
        for callback in self.callbacks:
            self._run_callback_safe(callback)

    def cancel(self):
        if self.done():
            return True
        self.is_cancelled = True
        self.evloop.call_soon(self._future_is_done)
        return False

    def cancelled(self):
        return self.is_cancelled

    def done(self):
        return (self.is_cancelled or self.has_valid_result
                or self.raised_exception)

    #
    # Pylint is confused by raised_exception initially being None.
    # pylint: disable = raising-bad-type
    #

    def result(self):
        if self.is_cancelled:
            raise _CancelledError()
        if self.has_valid_result:
            return self.result_obj
        if self.raised_exception:
            raise self.raised_exception
        raise _InvalidStateError()

    #
    # Re-enable the above error
    # pylint: enable = raising-bad-type
    #

    def exception(self):
        if self.is_cancelled:
            raise _CancelledError()
        if self.raised_exception:
            return self.raised_exception
        if self.has_valid_result:
            return None
        raise _InvalidStateError()

    def add_done_callback(self, callback):
        if self.done():
            self.evloop.call_soon(self._run_callback_safe, callback)
            return
        self.callbacks.append(callback)

    def remove_done_callback(self, callback):
        count = self.callbacks.count(callback)
        for _ in range(count):
            self.callbacks.remove(callback)
        return count

    def set_result(self, result):
        if self.done():
            raise _InvalidStateError()
        self.result_obj = result
        self.has_valid_result = True
        self.evloop.call_soon(self._future_is_done)

    def set_exception(self, exception):
        if self.done():
            raise _InvalidStateError()
        self.raised_exception = exception
        self.evloop.call_soon(self._future_is_done)
