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

import ConfigParser
import getopt
import shlex
import StringIO
import sys
import os

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.log import LOG

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

    def optionxform(self, option):
        return option

    def register_file(self, path):
        self.files.append(path)

    def merge_files(self):
        for path in self.files:
            try:
                self.read(path)
            except ConfigParser.ParsingError:
                LOG.exception()
                LOG.error("Can't parse config file: %s (see above)" % path)
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
                LOG.error("Missing section in option specified "
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
            LOG.error("No such option %s in section %s" % (option, section))
            sys.exit(1)
        return value

    def get_option_int(self, section, option):
        value = self.get_option(section, option)
        try:
            value = int(value)
        except ValueError:
            LOG.error("Option %s in section %s requires an integer argument"
              % (option, section))
            sys.exit(1)
        return value

    def get_option_uint(self, section, option):
        value = self.get_option_int(section, option)
        if value < 0:
            LOG.error("Option %s in section %s requires a non-negative "
              "integer argument" % (option, section))
            sys.exit(1)
        return value

    def get_option_float(self, section, option):
        value = self.get_option(section, option)
        try:
            value = float(value)
        except ValueError:
            LOG.error("Option %s in section %s requires a float argument"
              % (option, section))
            sys.exit(1)
        return value

    def get_option_bool(self, section, option):
        value = self.get_option(section, option)
        value = value.lower()
        if value not in TRUE_BOOLS and value not in FALSE_BOOLS:
            LOG.error("Option %s in section %s requires a boolean argument"
              % (option, section))
            sys.exit(1)
        return value in TRUE_BOOLS

# Test unit

USAGE = """Neubot options -- Test unit for options parser

Usage: neubot options [-Vv] [-D option[=value]] [-f file] [--help]

Options:
    -D option[=value]  : Set the value of the option option
    -f file            : Read options from file file
    --help             : Print this help screen and exit
    -V                 : Print version number and exit
    -v                 : Run the program in verbose mode

Macros:
    -D cast=type       : Attempt to cast all the other options to
                         the given type.  Type might be one of the
                         following:

                           bool   Cast to boolean
                           float  Cast to floating
                           int    Cast to integer
                           str    Cast to string (this is the default)
                           uint   Cast to unsigned integer

"""

VERSION = "Neubot 0.3.6\n"

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
             LOG.verbose()
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
                LOG.error("Invalid argument to -D cast: %s" % cast)
                sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)
