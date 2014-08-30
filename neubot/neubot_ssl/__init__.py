#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

try:
    from ssl import SSLContext
except ImportError:
    from ._context import _SSLContext as SSLContext

# The following should not fail in python >= 2.6
from ssl import PROTOCOL_SSLv23
from ssl import PROTOCOL_SSLv3
from ssl import PROTOCOL_TLSv1
