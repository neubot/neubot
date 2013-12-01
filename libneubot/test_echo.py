#!/usr/bin/env python
# Public domain, 2013 Simone Basso <bassosimone@gmail.com>

""" Test for NeubotEchoServer """

import ctypes

def main():
    """ Main function """
    dll = ctypes.CDLL("/usr/local/lib/libneubot.so")
    poller = dll.NeubotPoller_construct()
    dll.NeubotEchoServer_construct(poller, 1, "::1", "12345")
    dll.NeubotPoller_loop(poller)

if __name__ == "__main__":
    main()
