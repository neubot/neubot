#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

""" Neubot plugins protocol version 1. """

from neubot.backend import BACKEND
from neubot.config import CONFIG
from neubot.http.server import HTTP_SERVER
from neubot.negotiate.server import NEGOTIATE_SERVER
from neubot.notify import NOTIFIER
from neubot.poller import POLLER
from neubot.state import STATE

def _make_settings():
    """ Prepare the SETTINGS variable """
    settings = CONFIG.copy()
    settings["http.server.rootdir"] = ""
    return settings

def _run_something(spec, selector1, selector2, params):
    """ Helper function to run something """
    subspec = spec[selector1]
    if int(subspec["spec_version"]) != 1:
        raise RuntimeError("unhandled spec_version")
    runnable = subspec[selector2]
    for key in runnable["params"]:
        if key not in params:
            raise RuntimeError("missing param: %s", key)
        params[key] = runnable["params"][key](params[key])  # Cast
    runnable["run"](params, {
        "BACKEND": BACKEND,
        "HTTP_SERVER": HTTP_SERVER,
        "NEGOTIATE_SERVER": NEGOTIATE_SERVER,
        "NOTIFIER": NOTIFIER,
        "POLLER": POLLER,
        "SETTINGS": _make_settings(),
        "STATE": STATE,
    })

def run_testcontroller_client(spec, params):
    """ Runs the plugin's negotiator client """
    _run_something(spec, "test_controller", "client", params)

def run_testprovider_client(spec, params):
    """ Runs the plugin's negotiator client """
    _run_something(spec, "test_provider", "client", params)

def run_testcontroller_server(spec, params):
    """ Runs the plugin's negotiator server """
    _run_something(spec, "test_controller", "server", params)

def run_testprovider_server(spec, params):
    """ Runs the plugin's negotiator server """
    _run_something(spec, "test_provider", "server", params)
