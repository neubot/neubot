#!/usr/bin/env python
# Public domain, 2013 Simone Basso <bassosimone@gmail.com>

""" Test for NeubotPollable """

import ctypes
import os
import sys

LIBNEUBOT = ctypes.CDLL("/usr/local/lib/libneubot.so")

def read_callback(pollable):
    """ Read callback """
    data = os.read(0, 1024)
    if not data:
        LIBNEUBOT.NeubotPollable_close(pollable)
        return

    sys.stdout.write(data)

def close_callback(pollable):
    """ Close callback """
    poller = LIBNEUBOT.NeubotPollable_poller(pollable)
    LIBNEUBOT.NeubotPoller_break_loop(poller)

CALLBACK_T = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
READ_CALLBACK = CALLBACK_T(read_callback)
CLOSE_CALLBACK = CALLBACK_T(close_callback)

def main():
    """ Main function """

    poller = LIBNEUBOT.NeubotPoller_construct()

    pollable = LIBNEUBOT.NeubotPollable_construct(poller, READ_CALLBACK,
      None, CLOSE_CALLBACK, None)
    LIBNEUBOT.NeubotPollable_attach(pollable, 0)
    LIBNEUBOT.NeubotPollable_set_readable(pollable)

    LIBNEUBOT.NeubotPoller_loop(poller)

if __name__ == "__main__":
    main()
