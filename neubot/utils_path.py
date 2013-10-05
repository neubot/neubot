# neubot/utils_path.py

#
# Copyright (c) 2012-2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
#

''' Path management utils '''

#
# Python3-ready: yes
#

import collections
import logging
import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot import six

def depth_visit(prefix, components, visit):
    ''' Visit the subtree prefix/components[0]/components[1]... '''
    #
    # Append() guarantees that the result is always below prefix,
    # so the result of this function is below prefix as well.
    #
    # It is not an error to pass a component that contains one or
    # more path separators, except that subcomponents are not visited
    # in that case.
    #
    # The boolean second argument to visit is to distinguish between
    # leaf and ordinary nodes.
    #
    # This function is more strict than needed and generates an
    # error for input like '/var/www', ['a/b/c', '../d'], but we
    # don't care because that case doesn't happen in Neubot.
    #
    components = collections.deque(components)
    while components:
        prefix = append(prefix, components.popleft(), False)
        if prefix == None:
            raise RuntimeError("utils_path: depth_visit(): append() failed")
        visit(prefix, not components)
    return prefix

STRING_CLASS = six.u("").__class__

def decode(string, encoding):
    """ Decode STRING from ENCODING to UNICODE """
    logging.debug("utils_path: decode('%s', '%s')", string, encoding)
    try:
        string = string.decode(encoding)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        logging.warning("utils_path: decode() error", exc_info=1)
    else:
        return string

def encode(string, encoding):
    """ Encode STRING to ENCODING from UNICODE """
    logging.debug("utils_path: encode('%s', '%s')", string, encoding)
    try:
        string = string.encode(encoding)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        logging.warning("utils_path: encode() error", exc_info=1)
    else:
        return string

def possibly_decode(string, encoding):
    """ If needed, decode STRING from ENCODING to UNICODE """
    if string.__class__.__name__ == STRING_CLASS.__name__:
        return string
    return decode(string, encoding)

def append(rootdir, path, unquote_path):
    """ Append path to rootdir """

    logging.debug("utils_path: rootdir \"%s\"", rootdir)
    logging.debug("utils_path: path \"%s\"", path)

    #
    # ROOTDIR
    #

    rootdir = possibly_decode(rootdir, "utf-8")
    logging.debug("utils_path: unicode(rootdir): %s", rootdir)
    if not rootdir:
        return

    rootdir = os.path.normpath(rootdir)
    logging.debug("utils_path: normpath(rootdir): %s", rootdir)

    rootdir = os.path.realpath(rootdir)
    logging.debug("utils_path: realpath(rootdir): %s", rootdir)

    #
    # PATH
    #
    # 1) Neubot only and always uses ASCII paths;
    #
    # 2) after we unquote, the unicode string can contain some
    #    non-ASCII characters;
    #
    # 3) therefore we encode and decode again to make sure
    #    that we have an ASCII only path.
    #

    path = possibly_decode(path, "ascii")
    logging.debug("utils_path: ascii(path): %s", path)
    if not path:
        return

    if unquote_path:
        path = six.urlparse.unquote(path)
        logging.debug("utils_path: unquote(path): %s", path)

    #
    # Note: we encode() and decode() IN ANY CASE, because the original
    # path string can also be unicode, which means that the above
    # possibly_decode() invocation just returns the unicode string.
    #
    # BTW we MUST perform this step after we unquote(), because unquote()
    # may introduce non-ASCII chars into the string.
    #
    path = encode(path, "ascii")
    if not path:
        return
    path = decode(path, "ascii")
    if not path:
        return
    logging.debug("utils_path: make_sure_really_ascii(path): %s", path)

    #
    # JOINED
    #

    joined = join(rootdir, path)
    logging.debug("utils_path: joined = join(rootdir, path): %s", joined)

    joined = os.path.normpath(joined)
    logging.debug("utils_path: normpath(joined): %s", joined)

    joined = os.path.realpath(joined)
    logging.debug("utils_path: realpath(joined): %s", joined)

    if not joined.startswith(rootdir):
        logging.warning("utils_path: '%s' IS NOT below '%s'", joined, rootdir)
        return

    return joined

def normalize(string):
    ''' Normalize a pathname '''
    return os.path.normpath(string)

def join(left, right):
    ''' Join two paths '''
    return os.sep.join([left, right])

def main(args):
    """ Main function """
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    if len(args) < 3:
        sys.exit("usage: python neubot/utils_path.py prefix path [...]")
    if len(args) == 3:
        append(args[1], args[2], True)
    else:
        depth_visit(args[1], args[2:], lambda *args: None)

if __name__ == "__main__":
    main(sys.argv)
