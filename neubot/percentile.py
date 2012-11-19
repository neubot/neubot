# neubot/percentile.py

#
# Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>.
# Copyright (c) 2007 Wai Yip Tung.
#
# Released under the Python Software Foundation license and
# published on activestate.com.
#
# See http://code.activestate.com/recipes/511478/ (r2).
#

''' Compute percentile and median '''

import math

def percentile(vector, percent):
    ''' Find the percentile of a list of values '''
    if not vector:
        return None
    vector = sorted(vector)
    return _percentile(vector, percent)

def _percentile(vector, percent):
    ''' Find the percentile of a list of values '''
    pivot = (len(vector) - 1) * percent
    floor = math.floor(pivot)
    ceil = math.ceil(pivot)
    if floor == ceil:
        return vector[int(pivot)]
    val0 = vector[int(floor)] * (ceil - pivot)
    val1 = vector[int(ceil)] * (pivot - floor)
    return val0 + val1

def median(vector):
    ''' Find the median of a list of values '''
    return percentile(vector, 0.5)
