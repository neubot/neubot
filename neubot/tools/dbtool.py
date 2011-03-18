#!/usr/bin/env python

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

#
# Warning!  This script MUST NOT import any neubot class because
# we want people to be able to use it EVEN IF they have not installed
# neubot on their systems.  On the other hand, since this script
# is distributed in neubot/tools, other neubot modules might import
# stuff from this one.
#

#
# TODO It would be nice to add the -v command line option and to
# use it together with logging.stuff().  For example, it would be
# nice to uncomment the warning for SpeedtestCollect but to make
# it available only when we are verbose (i.e. it is an info and
# not a warning).
# TODO We should check the version number of the database in the
# config table.  As a rule of thumb, 1.x means speedtest only and
# 2.x means we also have support for BitTorrent.  For now, we
# just support 1.x and so we must at least print a warning if the
# database version is greater.
# TODO This file MUST be standalone, as explained above.  However
# this is a good place where to put generic code that deals with XML
# and with SQL, as well as the table definitions etc, and, in particular
# we might want to put here most of neubot/database.py to avoid the
# problem of keeping the two files in synch.
# TODO We need to create a command "dbtool" in neubot/main.py that
# invokes this file's main().  And we need to make sure that the
# `make install' command also installs this file.
#

# MaxMind
ASN_DATABASE = "/usr/local/share/GeoIP/GeoIPASNum.dat"
CITY_DATABASE = "/usr/local/share/GeoIP/GeoLiteCity.dat"

GEOIP_ERROR = \
"""Fatal error: cannot 'import GeoIP' into Python.
Please, install py-GeoIP and install also the related databases.
See <http://www.neubot.org/install-geoip> for more help.
"""

import unicodedata
import getopt
import sqlite3
import sys
import os
import uuid
import xml.dom.minidom

try:
    import GeoIP
except ImportError:
    sys.stderr.write(GEOIP_ERROR)
    sys.exit(1)

if __name__ == "__main__":
    sys.path.insert(0, ".")

def XXX_normalize_city_name(city):
    """
    This function is an hack and is here to avoid toxml("utf-8") failures
    when there are city names containing accented letters.  The hack consists
    of converting accented letters to normal letters and the solution I have
    chosen was one among the ones proposed in the following online thread
    <http://code.activestate.com/recipes/251871/>.  See in particular the post
    of Aaron Bentley, that says:
    >
    > [This solution] has the advantage that you don't need to enumerate any
    > particular conversions-- any accented latin characters will be reduced
    > to their base form, and non-ascii characters will be stripped.
    >
    > By normalizing to NFKD, we transform precomposed characters like
    > \u00C0 (LATIN CAPITAL LETTER A WITH GRAVE) into pairs of base letter
    > \u0041 (A) and combining character \u0300 (GRAVE accent).
    >
    > Converting to ascii using 'ignore' strips all non-ascii characters,
    > e.g. the combining characters. However, it will also strip other
    > non-ascii characters, so if there are no latin characters in the input,
    > the output will be empty.
    >
    Note that we know that GeoIP returns LATIN-1 strings (it's possible
    to guess that reading GeoIP.h).  In order to test what happens without
    this function, just make this one a no-op and make sure that there is
    at least a city name that contains an accented letter.
    """
    city = unicode(city, "latin-1")
    return unicodedata.normalize("NFKD", city).encode("ASCII", "ignore")

class Anonymizer(object):

    """
    Map a unique identifier into a unique integer and remember the
    mapping, so that the same identifier always maps to the same unique
    integer.
    """

    def __init__(self):
        self.mapping = {}
        self.last = 0

    def anonymize(self, identifier):
        if not identifier in self.mapping:
            self.mapping[identifier] = str(self.last)
            self.last = self.last + 1
        return self.mapping[identifier]

class CityResolver(object):

    """
    Map an internet address to a (CountryCode,Region,City) tuple.
    """

    def __init__(self, filename):
        if not os.path.isfile(filename):
            sys.stderr.write("CityResolver: %s: No such file or directory\n" %
                filename)
            sys.stderr.write("See <http://www.neubot.org/install-geoip> "
                "for more help\n")
            exit(1)
        self.handle = GeoIP.open(filename, GeoIP.GEOIP_STANDARD)

    def resolve(self, address):
        record = self.handle.record_by_addr(address)
        if not record:
            sys.stderr.write("CityResolver: %s not found\n" % address)
            return None
        record["city"] = XXX_normalize_city_name(record["city"])
        ret = record["country_code"], record["region"], record["city"]
        return ret

class ASNResolver(object):

    """
    Map an internet address to Autonomous System Number and Autonomous
    System name and returns the (number, name) tuple.
    """

    def __init__(self, filename):
        if not os.path.isfile(filename):
            sys.stderr.write("ASNResolver: %s: No such file or directory\n" %
                filename)
            sys.stderr.write("See <http://www.neubot.org/install-geoip> "
                "for more help\n")
            exit(1)
        self.handle = GeoIP.open(filename, GeoIP.GEOIP_STANDARD)

    def resolve(self, address):
        record = self.handle.org_by_addr(address)
        if not record:
            sys.stderr.write("ASNResolver: %s not found\n" % address)
            return None
        try:
            asn, name = record.split(" ", 1)
        except ValueError:
            sys.stderr.write("ASNResolver: %s: can't split" % record)
            return None
        return asn, name

class SpeedtestResult(object):

    """
    Represent the result of a speedtest.
    """

    def __init__(self):
        self.client = ""
        self.timestamp = 0
        self.internalAddress = ""
        self.realAddress = ""
        self.realAddressRegion = ""
        self.realAddressCountryCode = ""
        self.realAddressCity = ""
        self.realAddressASN = ""
        self.realAddressASName = ""
        self.remoteAddress = ""
        self.remoteAddressRegion = ""
        self.remoteAddressCountryCode = ""
        self.remoteAddressCity = ""
        self.remoteAddressASN = ""
        self.remoteAddressASName = ""
        self.connectTime = 0.0
        self.latency = 0.0
        self.downloadSpeed = 0.0
        self.uploadSpeed = 0.0

def XML_append_attribute(document, element, name, value):
    """
    Append to <element> an element with tagName <name> that contains
    a text node with value <value>.  All nodes are created in the context
    of the document <document>.  While at it, we also try to indent
    the resulting XML file in a way similar to what Firefox does in order
    to make it more human readable.
    """
    indent = document.createTextNode("    ")
    element.appendChild(indent)
    child_element = document.createElement(name)
    element.appendChild(child_element)
    text_node = document.createTextNode(value)
    child_element.appendChild(text_node)
    newline = document.createTextNode("\r\n")
    element.appendChild(newline)

def XML_is_leaf(node):
    """
    Returns True if <node> is an element and is a leaf, i.e. does not
    contain any child element node.
    """
    node.normalize()
    if node.nodeType != node.ELEMENT_NODE:
        return False
    for node in node.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            return False
    return True

def XML_leaf_to_attribute(node):
    """
    Return the (name,value) tuple you can extract from the leaf
    element node <node>.
    """
    vector = []
    name = node.tagName
    for node in node.childNodes:
        if node.nodeType != node.TEXT_NODE:
            continue
        vector.append(node.data)
    value = "".join(vector).strip()
    return name, value

class SpeedtestResultXML(SpeedtestResult):

    """
    Marshal/unmarshal speedtest results in XML.
    """

    def __str__(self):
        document = xml.dom.minidom.parseString("<speedtestResult/>")
        root = document.documentElement
        newline = document.createTextNode("\r\n")
        root.appendChild(newline)
        for name, value in vars(self).items():
            XML_append_attribute(document, root, name, str(value))
        try:
            data = root.toxml("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            sys.stderr.write("warning: unicode encode/decode error\n")
            data = ""
        return data

    def __init__(self, data):
        SpeedtestResult.__init__(self)
        document = xml.dom.minidom.parseString(data)
        root = document.documentElement
        if root.tagName == "SpeedtestCollect":
            #sys.stderr.write("warning: Old root element name: %s\n" % root.tagName)
            root.tagName = "speedtestResult"
        for node in root.childNodes:
            if node.nodeType != node.ELEMENT_NODE:
                continue
            if not XML_is_leaf(node):
                sys.stderr.write("warning: Ignoring non-leaf: %s\n" % node.tagName)
                continue
            name, value = XML_leaf_to_attribute(node)
            if not hasattr(self, name):
                sys.stderr.write("warning: Ignoring unknown attr: %s\n" % name)
                continue
            setattr(self, name, value)

class Configuration(object):

    """
    Hold the configuration of this Python module.
    """

    asn_database = ASN_DATABASE
    city_database = CITY_DATABASE

    anonymize_address = Anonymizer().anonymize
    anonymize_uuid = Anonymizer().anonymize
    asn_resolver = None
    city_resolver = None

    def init_db(self):
        self.asn_resolver = ASNResolver(self.asn_database)
        self.city_resolver = CityResolver(self.city_database)

    def resolve_asn(self, address):
        return self.asn_resolver.resolve(address)

    def resolve_city(self, address):
        return self.city_resolver.resolve(address)

def FILTER_noop(conf, result):
    """
    Do not filter.
    """

def FILTER_timestamp(conf, result):
    """
    Make sure timestamp is an integer.  There is a bug in certain
    versions of neubot where the timestamp is a floating point number
    on certain platforms.
    """
    result.timestamp = str(int(float(result.timestamp)))

def FILTER_anonymize(conf, result):
    """
    Anonymize speedtest result as follows:
      1. Replace client UUID with a unique integer;
      2. Replace internal address with a unique integer;
      3. For each address in realAddress remoteAddress:
         3.1 Add geograhical information for address;
         3.2 Add autonomous system information for address;
         3.2 Replace address with a unique integer;
    """
    result.client = conf.anonymize_uuid(result.client)
    result.internalAddress = conf.anonymize_address(result.internalAddress)
    geo_info = conf.resolve_city(result.realAddress)
    if geo_info:
        result.realAddressCountryCode = geo_info[0]
        result.realAddressRegion = geo_info[1]
        result.realAddressCity = geo_info[2]
    asn_info = conf.resolve_asn(result.realAddress)
    if asn_info:
        result.realAddressASN = asn_info[0]
        result.realAddressASName = asn_info[1]
    result.realAddress = conf.anonymize_address(result.realAddress)
    geo_info = conf.resolve_city(result.remoteAddress)
    if geo_info:
        result.remoteAddressCountryCode = geo_info[0]
        result.remoteAddressRegion = geo_info[1]
        result.remoteAddressCity = geo_info[2]
    asn_info = conf.resolve_asn(result.remoteAddress)
    if asn_info:
        result.remoteAddressASN = asn_info[0]
        result.remoteAddressASName = asn_info[1]
    result.remoteAddress = conf.anonymize_address(result.remoteAddress)

class ProcessorInterface(object):
    """
    Common interface for all processors.
    """

    def init(self, parameters):
        """
        Initialize the processor, e.g. print something before
        the data, or open a file.
        The param <parameters> is a dictionary that holds optional
        parameters for the initializer.
        """

    def feed(self, result):
        """
        Do something with results.
        """

    def finish(self):
        """
        Finalize the processor, e.g. print something after the
        data, or close a file.
        """

class XMLizer(ProcessorInterface):
    """
    XMLifies the content of the result table.
    """

    def __init__(self, outfile):
        self.outfile = outfile

    def init(self, parameters):
        self.outfile.write('<results timeUnit="s" speedUnit="iByte/s">\r\n')

    def feed(self, result):
        self.outfile.write(str(result))
        self.outfile.write("\r\n")

    def finish(self):
        self.outfile.write("</results>\r\n")

class UUIDCounter(ProcessorInterface):
    """
    Counts the number of UUIDs every <threshold> time.
    """

    def __init__(self, outfile):
        self.outfile = outfile
        self.last = 0
        self.uuids = set()

    def init(self, parameters):
        if 'threshold' in parameters:
            self.threshold = parameters['threshold']
        else:
            self.threshold = 86400

    def feed(self, result):
        current = int(result.timestamp)
        if self.last == 0 or current - self.last > self.threshold:
            if self.last > 0:
                self.outfile.write("%d %d\r\n" % (self.last, len(self.uuids)))
            self.uuids.clear()
            self.last = current
        self.uuids.add(result.client)

    def finish(self):
        self.outfile.write("%d %d\r\n" % (self.last, len(self.uuids)))

def DB_walker(conf, filename, processor, filters, parameters):
    """
    Walk the tuples in the results table of the database at <filename>
    and then filter each tuple through the registered <filters> and finally
    pass the result to the specified <processor> with <parameters>.
    """
    processor.init(parameters)
    connection = sqlite3.connect(filename)
    reader = connection.cursor()
    reader.execute("SELECT result FROM results WHERE tag = 'speedtest';")
    for data in reader:
        # data is a tuple
        result = SpeedtestResultXML(data[0])
        for func in filters:
            func(conf, result)
        processor.feed(result)
    reader.close()
    processor.finish()

#
# Warning! Do not expect these command line options to stay like
# this for too much time.  I'd like to rework them because if we add
# a new option for each different analysis this is going to explode
# and we will soon run out of letters.  And also these options are
# not orthogonal which is bad from the user point of view.
#

VERSION = "0.3.6"

USAGE = """Usage: @PROGNAME@ [-CnV] [-T threshold] [--help] database
"""

HELP = USAGE + """
Options:
  -C          : Count unique UUIDs per day (see also -T).
  -n          : Do not anonymize the database.
  --help      : Print this help screen and exit.
  -T treshold : Modifier for -C: count the number of unique UUIDs
                every treshold seconds rather than every day.
  -V          : Print version number and exit.

"""

#
# The rationale of the main() function is that neubot/main.py can
# `from neubot.tools import dbtool' and then can `dbtool.main()' so
# this module is reachable from /usr/bin/neubot
#

def main(args):
    parameters = {}
    count = False
    anon = True

    filters = [ FILTER_timestamp ]
    try:
        options, arguments = getopt.getopt(args[1:], "CnT:V", ["help"])
    except getopt.error:
        sys.stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        sys.exit(1)
    for name, value in options:
        if name == "-C":
            count = True
            continue
        if name == "-n":
            anon = False
            continue
        if name == "-T":
            try:
                threshold = int(value)
            except ValueError:
                threshold = -1
            if threshold < 0:
                sys.stderr.write("error: threshold must be a positive integer\n")
                sys.exit(1)
            parameters['threshold'] = threshold
            continue
        if name == "--help":
            sys.stdout.write(HELP.replace("@PROGNAME@", args[0]))
            sys.exit(0)
            continue
        if name == "-V":
            sys.stdout.write(VERSION + "\n")
            sys.exit(0)
            continue
    if len(arguments) != 1:
        sys.stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        sys.exit(1)
    if anon and not count:
        filters.append(FILTER_anonymize)
    filename = arguments[0]
    conf = Configuration()
    conf.init_db()
    if count:
        processor = UUIDCounter(sys.stdout)
    else:
        processor = XMLizer(sys.stdout)

    DB_walker(conf, filename, processor, filters, parameters)

if __name__ == "__main__":
    main(sys.argv)
