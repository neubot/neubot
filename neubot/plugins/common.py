#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

""" Common code for managing Neubot plugins """

import logging
import sys

from . import v1

def probe_plugin(name):
    """ Probe the specified plugin and return its spec """

    modname = "mod_" + name

    try:
        __import__(modname)
    except ImportError:
        logging.warning("import failed", exc_info=1)
        return {}

    try:
        plugin_spec = sys.modules[modname].neubot_plugin_spec
    except AttributeError:
        logging.warning("missing `neubot_plugin_spec` name", exc_info=1)
        return {}

    try:
        spec = plugin_spec()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except:
        logging.warning("`neubot_plugin_spec`() failed", exc_info=1)
        return {}

    logging.debug("")
    logging.debug("name: %s", spec["name"])
    logging.debug("short_description: %s", spec["short_description"])
    logging.debug("author: %s", spec["author"])
    logging.debug("version: %s", spec["version"])
    logging.debug("spec_version: %s", spec["spec_version"])
    logging.debug("")

    return spec

def run_testcontroller_client(spec, params):
    """ Run the plugin's TestController client """
    if int(spec["spec_version"]) != 1:
        raise RuntimeError("unhandled spec_version")
    v1.run_testcontroller_client(spec, params)

def run_testprovider_client(spec, params):
    """ Run the plugin's TestProvider client """
    if int(spec["spec_version"]) != 1:
        raise RuntimeError("unhandled spec_version")
    v1.run_testprovider_client(spec, params)

def run_testcontroller_server(spec, params):
    """ Run the plugin's TestController client """
    if int(spec["spec_version"]) != 1:
        raise RuntimeError("unhandled spec_version")
    v1.run_testcontroller_server(spec, params)

def run_testprovider_server(spec, params):
    """ Run the plugin's TestProvider server """
    if int(spec["spec_version"]) != 1:
        raise RuntimeError("unhandled spec_version")
    v1.run_testprovider_server(spec, params)
