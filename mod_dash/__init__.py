# mod_dash/__init__.py

#
# Copyright (c) 2013-2014
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

""" The MPEG DASH test """

from .client import DASH_RATES
from .client import TestControllerClient
from .client import TestProviderClient

from .server import TestProviderServerGlue
from .server import TestProviderServer
from .server import TestControllerServer

def _run_test_provider_client(params, context):
    """ Run DASH TestProvider client """
    client = TestProviderClient(context["POLLER"], None, DASH_RATES,
        context["STATE"])
    client.configure(context["SETTINGS"])
    client.connect((params["address"], params["port"]))

def _run_test_controller_client(params, context):
    """ Run DASH TestController client """
    client = TestControllerClient(context["POLLER"], context["BACKEND"],
        context["NOTIFIER"], context["STATE"])
    client.configure(context["SETTINGS"])
    client.connect((params["address"], params["port"]))

def _run_test_provider_server(params, context):
    """ Run DASH TestProvider server """
    provider = TestProviderServer(context["POLLER"], None)
    provider.configure(context["SETTINGS"])
    provider.listen((params["address"], params["port"]))

def _run_test_controller_server(params, context):
    """ Run DASH TestController server """

    controller = TestControllerServer(context["BACKEND"])
    context["NEGOTIATE_SERVER"].register_module("dash", controller)

    provider = TestProviderServerGlue(context["POLLER"], controller)
    provider.configure(context["SETTINGS"])
    context["HTTP_SERVER"].register_child(provider, "/dash")

def neubot_plugin_spec():
    """ Returns the plugin spec """
    return {
        "spec_version": 1.0,
        "name": "dash",
        "short_description": "Neubot MPEG DASH test",
        "author": "Simone Basso <bassosimone@gmail.com>",
        "version": 1.0,
        "www": {
            "spec_version": 1.0,
            "description": "www/dash.html",
            "results_producer": "www/dash.json",
        },
        "backend": {
            "spec_version": 2.0,
        },
        "test_provider": {
            "spec_version": 1.0,
            "client": {
                "run": _run_test_provider_client,
                "params": {
                    "address": str,
                    "port": int,
                },
            },
            "server": {
                "run": _run_test_provider_server,
                "params": {
                    "address": str,
                    "port": int,
                },
            },
        },
        "test_controller": {
            "spec_version": 1.0,
            "client": {
                "run": _run_test_controller_client,
                "params": {
                    "address": str,
                    "port": int,
                },
            },
            "server": {
                "run": _run_test_controller_server,
                "params": {
                },
            },
        },
    }
