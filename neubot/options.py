# neubot/options.py

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
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

"""
neubot.options
==============

Neubot options parser
^^^^^^^^^^^^^^^^^^^^^

:Manual section: 3
:Date: 2011-01-07
:Manual group: Neubot manual
:Version: Neubot 0.3.3

SYNOPSYS
````````

|   from neubot.options import *

DESCRIPTION
```````````

Neubot can read options from various configuration files, from the
environment, and from command line.

Options canonical form is *section.option=value*.  Where section
is the name of a Neubot module, option is the name of a scalar
variable within that module, and value is a string.  For example,
the option *database.path=/var/neubot/database.sqlite3* specifies
that the value of the variable *path* within *neubot/database.py*
should be set to */var/neubot/database.sqlite3*.

However, there are cases when options might not be specified in
their canonical form for convenience.

Setting default values
''''''''''''''''''''''

You might want to set some default values for the options.  To do
that, use the *set_option* method, that receives three arguments,
the name of the section, the name of the option, and the value.

Reading a configuration file
''''''''''''''''''''''''''''

You invoke the method *register_file* to registed a configuration
file that must be read later.  There is no limit on the maximum
number of configuration files you can register.  This method takes
just one argument, the configuration file path.

The method *merge_files* receives no arguments and reads all the
registed configuration files in FIFO order.

The format of a configuration file is as follows::

  [database]
  path = /var/neubot/database.sqlite3

  [ui]
  port = 9774
  address = 127.0.0.1

Reading the sample configuration file above will result in the
options *database.path*, *ui.port*, and *ui.address* being set.

The method *merge_files* prints an error using *neubot.log* and
exits if there is an error parsing an existing configuration file.
However, it will skip silently a configuration file that does not
exist.

Reading from environment
''''''''''''''''''''''''

To read options from the environment you invoke the method
*merge_environ*, which receives no arguments.  This method will
read options from the environment variable *NEUBOT_OPTIONS*.

The format of such variable is as follows::

  $ export NEUBOT_OPTIONS="ui.address=0.0.0.0 ui.port=9000"

Reading options from the variable in the example above will result
in the options *ui.address* and *ui.port* being set.

The method prints an error using *neubot.log* and exits if the
content of the environment variable is not well formed.

Reading from commandline
''''''''''''''''''''''''

Command line options may not be specified in canonical form.  In
particular, it is possible to omit both the section and the value.
If the section is missing a default value is used.  If the value
is missing, it is assumed an implied value of True.

So, assuming that the default section is *foo* the following command
line::

  $ neubot command -D foo.interval=3 -D foo.enable=True -Dbar.x=3.1

is equivalent to::

  $ neubot command -Dinterval=3 -Dfoo.enable -Dbar.x=3.1

When parsing command line options, you register the value of
interesting options using *register_opt*.  This method receives two
parameters, the value of the option and the default section name
to be used if needed.

Then, at a later time, you merge the values of the interesting
command line options invoking the *merge_opts* method, that takes
no arguments.

Getting options
'''''''''''''''

Once you have merged options from configuration files, environment,
and command line, you might want to retrieve the value of such
options.  In order to do that use the *get_option* method.  This
method receives two parameters, the section and the name of the
option.  This method always returns a string.  In addition there
are convenience methods to cast the value to something else.  Use
*get_option_int* to cast to integer, *get_option_uint* to cast
to an unsigned integer, *get_option_bool* to cast to boolean, and
*get_option_float* to cast to float.

These methods print an error using *neubot.log* and exit if the
requested option does not exist.

INTERFACE
`````````

In conclusion, here's the interface that we have described in this
manual page::

    class OptionParser(object):

        def set_option(self, section, option, value):
            "Sets the value of section.option to value."

        def register_file(self, path):
            "Register config file at path to be read later."

        def merge_files(self):
            "Merge the content of all the registered config files."

        def merge_environ(self):
            "Merge options from the NEUBOT_OPTION environment variable."

        def register_opt(self, option, default_sect):
            "Register command line option eventually using default_sect."

        def merge_opts(self):
            "Merge all registered command line options."

        def get_option(self, section, option):
            "Return the value of section.option or exits if not found."

        def get_option_int(self, section, option):
            "Same as above but also try to cast to int."

        def get_option_uint(self, section, option):
            "Same as above but also try to cast to unsigned int."

        def get_option_bool(self, section, option):
            "Same as above but also try to cast to boolean."

        def get_option_float(self, section, option):
            "Same as above but also try to cast to float."

BUGS
````

This module does not work reliably unless section names and option
names are all lowercase.  This is due to the interaction between this
module and ConfigParser.RawConfigParser.

AUTHOR
``````

| Simone Basso <bassosimone@gmail.com>

SEE ALSO
````````

| neubot(1)

"""

import ConfigParser
import getopt
import shlex
import StringIO
import sys
import os

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot import log

FALSE_BOOLS = [ "0", "no", "false", "off" ]
TRUE_BOOLS  = [ "1", "yes", "true", "on"  ]

class OptionParser(ConfigParser.RawConfigParser):

    #
    # Implementation note.  Yes, it would be more effective to
    # override as much as we can RawConfigParser.  But there are
    # subtle differences.  For example, when we set an option
    # we autocreate the section if it does not exist and, instead,
    # RawConfigParser raises an exception in this case.  Then,
    # we don't want to surprise RawConfigParser users and so, we
    # have implemented something with different names.
    #

    def __init__(self):
        ConfigParser.RawConfigParser.__init__(self)
        self.cmdline = StringIO.StringIO()
        self.cmdline.write("[__cmdline__]\n")
        self.files = []

    def set_option(self, section, option, value):
        if not self.has_section(section):
            self.add_section(section)
        self.set(section, option, value)

    def register_file(self, path):
        self.files.append(path)

    def merge_files(self):
        for path in self.files:
            try:
                self.read(path)
            except ConfigParser.ParsingError:
                log.exception()
                log.error("Can't parse config file: %s (see above)" % path)
                sys.exit(1)

    def merge_environ(self):
        if not "NEUBOT_OPTIONS" in os.environ:
            return
        for orig in shlex.split(os.environ["NEUBOT_OPTIONS"]):
            var = orig
            if not "=" in var:
                var = var + "=TRUE"
            key, value = var.split("=", 1)
            if not "." in key:
                log.error("Missing section in option specified "
                  "via environment: %s" % orig)
                sys.exit(1)
            section, option = key.split(".", 1)
            self.set_option(section, option, value)

    def register_opt(self, var, section):
        if not "=" in var:
            var = var + "=TRUE"
        key, value = var.split("=", 1)
        if not "." in key:
            key = section + "." + key
        if not value.endswith("\n"):
            value = value + "\n"
        var = key + "=" + value
        self.cmdline.write(var)

    def merge_opts(self):
        self.cmdline.seek(0)
        self.readfp(self.cmdline, "Options specified via command line")
        for key in self.options("__cmdline__"):
            value = self.get("__cmdline__", key)
            section, option = key.split(".", 1)
            self.set_option(section, option, value)
        self.remove_section("__cmdline__")

    def get_option(self, section, option):
        try:
            value = self.get(section, option)
        except ConfigParser.NoOptionError:
            log.error("No such option %s in section %s" % (option, section))
            sys.exit(1)
        return value

    def get_option_int(self, section, option):
        value = self.get_option(section, option)
        try:
            value = int(value)
        except ValueError:
            log.error("Option %s in section %s requires an interger argument"
              % (option, section))
            sys.exit(1)
        return value

    def get_option_uint(self, section, option):
        value = self.get_option_int(section, option)
        if value < 0:
            log.error("Option %s in section %s requires a non-negative "
              "integer argument" % (option, section))
            sys.exit(1)
        return value

    def get_option_float(self, section, option):
        value = self.get_option(section, option)
        try:
            value = float(value)
        except ValueError:
            log.error("Option %s in section %s requires a float argument"
              % (option, section))
            sys.exit(1)
        return value

    def get_option_bool(self, section, option):
        value = self.get_option(section, option)
        value = value.lower()
        if value not in TRUE_BOOLS and value not in FALSE_BOOLS:
            log.error("Option %s in section %s requires a boolean argument"
              % (option, section))
            sys.exit(1)
        return value in TRUE_BOOLS

__all__ = [ "OptionParser" ]

# Test unit

USAGE = """Neubot options -- Test unit for options parser

Usage: neubot options [-Vv] [-D option[=value]] [-f file] [--help]

Options:
    -D option[=value]  : Set the value of the option option.
    -f file            : Read options from file file.
    --help             : Print this help screen and exit.
    -V                 : Print version number and exit.
    -v                 : Run the program in verbose mode.

Options:
    -D cast=type       : Attempt to cast all the other options to
                         the given type.  Type might be one of the
                         following:

                           bool   Cast to boolean
                           float  Cast to floating
                           int    Cast to integer
                           str    Cast to string (this is the default)
                           uint   Cast to unsigned integer

"""

VERSION = "Neubot 0.3.3\n"

def _write(section, option, value):
    sys.stdout.write("%s.%s=%s\n" % (section, option, str(value)))

def main(args):

    conf = OptionParser()
    conf.set_option("options", "cast", "str")

    try:
        options, arguments = getopt.getopt(args[1:], "D:f:Vv", ["help"])
    except getopt.GetoptError:
        sys.stderr.write(USAGE)
        sys.exit(1)

    if len(options) == 0:
        sys.stdout.write(USAGE)
        sys.exit(0)
    if len(arguments) != 0:
        sys.stderr.write(USAGE)
        sys.exit(1)

    for name, value in options:
        if name == "-D":
             conf.register_opt(value, "options")
             continue
        if name == "-f":
             conf.register_file(value)
             continue
        if name == "--help":
             sys.stdout.write(USAGE)
             sys.exit(0)
        if name == "-V":
             sys.stdout.write(VERSION)
             sys.exit(0)
        if name == "-v":
             log.verbose()
             continue

    conf.merge_files()
    conf.merge_environ()
    conf.merge_opts()

    cast = conf.get_option("options", "cast")

    for section in conf.sections():
        for option in conf.options(section):
            if section == "options" and option == "cast":
                continue

            if cast == "bool":
                _write(section, option, conf.get_option_bool(section,option))
            elif cast == "float":
                _write(section, option, conf.get_option_float(section, option))
            elif cast == "int":
                _write(section, option, conf.get_option_int(section, option))
            elif cast == "str":
                _write(section, option, conf.get_option(section, option))
            elif cast == "uint":
                _write(section, option, conf.get_option_uint(section, option))
            else:
                log.error("Invalid argument to -D cast: %s" % cast)
                sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)
