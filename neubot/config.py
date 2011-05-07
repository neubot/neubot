# neubot/config.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
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
# =================================================================
# The update() method of ConfigDict is a derivative work
# of Python 2.5.2 Object/dictobject.c dict_update_common().
#
# Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008
# Python Software Foundation; All Rights Reserved.
#
# I've put a copy of Python LICENSE file at doc/LICENSE.Python.
# =================================================================
#

import itertools
import os
import shlex

from neubot.log import LOG
from neubot.database import table_config
from neubot import utils

def string_to_kv(string):

    """Convert string to (key,value).  Returns the empty tuple if
       the string is a comment or contains just spaces."""

    string = string.strip()
    if not string or string[0] == "#":
        return tuple()
    kv = string.split("=", 1)
    if len(kv) == 1:
        kv.append("True")
    return tuple(kv)

def kv_to_string(kv):

    """Convert (key,value) to string.  Adds a trailing newline so
       we can pass the return value directly to fp.write()."""

    return "%s=%s\n" % (utils.stringify(kv[0]), utils.stringify(kv[1]))


class ConfigDict(dict):

    """Modified dictionary.  At the beginning we fill it with default
       values, e.g. when a new module is loaded.  Then, when we update
       this dictionary we want new values to have the same type of the
       old ones.  We perform the check when the dictionary is updated
       and not when it is accessed because in the latter case we might
       delay errors and that would be surprising."""

    def __setitem__(self, key, value):
        if key in self:
            ovalue = self[key]
            cast = utils.smart_cast(ovalue)
        else:
            ovalue = "(none)"
            cast = utils.smart_cast(value)
        value = cast(value)
        LOG.debug("config: %s: %s -> %s" % (key, ovalue, value))
        dict.__setitem__(self, key, value)

    def update(self, *args, **kwds):
        if args:
            arg = tuple(args)[0]
            if hasattr(arg, "keys"):
                arg = arg.iteritems()
            map(lambda t: self.__setitem__(t[0], t[1]), arg)
        if kwds:
            self.update(kwds.iteritems())


class ConfigError(Exception):
    pass


class Config(object):

    """Configuration manager.  Usually there is just one instance
       of this class, named CONFIG, that gatekeeps the configuration.
       The expected usage is as follows::

           from neubot.config import CONFIG
           ...

           #
           # Each module needs to export its set of properties
           # along with their default values.
           #
           CONFIG.register_defaults({
             "module.enabled": True,
             "module.address": "127.0.0.1",
             "module.port": 9774,
           })
           ...

               #
               # When you create a new instance of a test, get
               # a _copy_ of all the relevant variables and then
               # create the instance using such copy.
               # Note that the returned copy _is_ a dictionary,
               # so you SHOULD employ the get() pattern used below
               # to increment your module robustness.
               # Of course you can add/remove/change values since
               # you are working on a copy.
               #
               def create_test(self):
                   ...
                   k = CONFIG.copy()
                   if k.get("enabled", True):
                       self.listen(k.get("module.address", "127.0.0.1"),
                         k.get("module.port", 9774))
                       k["module.ntries"] = 7
                   ...

               #
               # In certain cases -- such as when you want to check
               # whether you MUST interrupt the test or not -- it makes
               # tremendous sense to check the current configuration
               # instead of using the copy.
               # For this cases, Config implements a dict-like get()
               # method and you MUST use it.
               #
               def periodic(self):
                   ...
                   if not CONFIG.get("enabled", True):
                       self.interrupt_test()
                   ...

           #
           # When your module is starting up, register all
           # the ``-D property`` command line options.
           #
           ...
           for name, value in options:
               ...
               if name == "-D":
                   CONFIG.register_property(value, "module")
                   continue
               ...

           #
           # When you have processed command line options, you
           # should merge the default configuration with input
           # coming from the database (if any), environment, and
           # command line (in this order!)
           #
           if database.dbm:
               CONFIG.merge_database(database.dbm)
           CONFIG.merge_environ()
           CONFIG.merge_properties()
           ...

               #
               # You can modify the configuration when the program
               # is running using the API.  The input is a dictionary
               # containing the changes.  Note that we raise ConfigError
               # when something goes wrong.
               # Note that if database.dbm is not None the changes
               # are propagated to the database.
               # The principle is that:
               #
               # 1. the last change rules,
               # 2. only updates from API affect the database.
               #
               def update_from_api(self, kvstore):
                   CONFIG.merge_api(kvstore, database.dbm)
                   ...

           #
           # Finally, we can read/write from/to file and that
           # allows to export/import the configuration, should
           # you want to clone it.
           # It is very useful to write the current config to
           # a database as well.
           #
           CONFIG.merge_fp(sys.stdin)
           ...
           CONFIG.store_fp(sys.stdout)
           ...
           CONFIG.store_database(sqlite3.connect("database.sqlite3"))

       Yeah.  This is all you need to know to use this class and
       hence this module."""

    def __init__(self):
        self.properties = []
        self.conf = ConfigDict()
        self.descriptions = {}

    def register_defaults(self, kvstore):
        self.conf.update(kvstore)

    def register_descriptions(self, d):
        self.descriptions.update(d)

    def copy(self):
        return dict(self.conf)

    def get(self, key, defvalue):
        return self.conf.get(key, defvalue)

    def register_property(self, prop, module=""):
        if module and not prop.startswith(module):
            prop = "%s.%s" % (module, prop)
        self.properties.append(prop)

    def merge_fp(self, fp):
        map(self.merge_kv, itertools.imap(string_to_kv, fp))

    def merge_database(self, database):
        table_config.walk(database, self.merge_kv)

    def merge_environ(self):
        map(self.merge_kv, itertools.imap(string_to_kv,
          shlex.split(os.environ.get("NEUBOT_OPTIONS",""))))

    def merge_properties(self):
        map(self.merge_kv, itertools.imap(string_to_kv, self.properties))

    def merge_api(self, dictlike, database=None):
        # enforce all-or-nothing
        map(lambda t: self.merge_kv(t, dry=True), dictlike.iteritems())
        map(self.merge_kv, dictlike.iteritems())
        if database:
            table_config.update(database, dictlike.iteritems())

    def merge_kv(self, t, dry=False):
        if t:
            key, value = t
            if not dry:
                self.conf[key] = value

            else:
                try:
                    ovalue = self.conf[key]
                    cast = utils.smart_cast(ovalue)
                    cast(value)
                except KeyError:
                    raise ConfigError("No such property: %s" % key)
                except TypeError:
                    raise ConfigError("Old value '%s' for property '%s'"
                      " has the wrong type" % (ovalue, key))
                except ValueError:
                    raise ConfigError("Invalid value '%s' for property '%s'" %
                                      (value, key))

    def store_fp(self, fp):
        map(fp.write, itertools.imap(kv_to_string, self.conf.iteritems()))

    def store_database(self, database):
        table_config.update(database, self.conf.iteritems(), clear=True)

    def print_descriptions(self, fp):
        fp.write("Properties (current value in square brackets):\n")
        for key in sorted(self.descriptions.keys()):
            description = self.descriptions[key]
            value = self.conf[key]
            fp.write("    %-28s: %s [%s]\n" % (key, description, value))
        fp.write("\n")


CONFIG = Config()

CONFIG.register_defaults({
    "enabled": True,
    "privacy.informed": False,
    "privacy.can_collect": False,
    "privacy.can_share": False,
})
CONFIG.register_descriptions({
    "enabled": "Enable Neubot to perform transmission tests",
    "privacy.informed": "You assert that you have read and understood the above privacy policy",
    "privacy.can_collect": "You give Neubot the permission to collect your Internet address",
    "privacy.can_share": "You give Neubot the permission to share your Internet address with the Internet community",
})
