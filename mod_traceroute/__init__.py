
""" Neubot's traceroute module """

#
# Note: one problem of this implementation is that we leak the open file
# descriptors and environment variables to traceroute. I am unsure whether
# this is a real problem for Neubot, or not.
#

import logging
import os
import subprocess
import tempfile
import time

def _run_traceroute(params, context):
    """ Run the traceroute test """
    argv = ["/usr/bin/traceroute", params["address"]]
    fout = tempfile.TemporaryFile()
    ferror = tempfile.TemporaryFile()
    proc = subprocess.Popen(argv, stdout=fout, stderr=ferror)
    started = time.time()

    def check_process():
        """ Checks the process state """

        if proc.poll() == None:
            logging.debug("traceroute: running...")
            if time.time() - started > params["timeout"]:
                proc.kill()
            context["POLLER"].sched(1.0, check_process)
            return

        fout.seek(0, os.SEEK_SET)
        lines = []
        for line in fout:
            logging.debug("traceroute stdout: %s", line)
            lines.append(line)
        context["BACKEND"].store_generic("traceroute", {"lines": lines})

        ferror.seek(0, os.SEEK_SET)
        for line in ferror:
            logging.warning("traceroute stderr: %s", line.rstrip())
        context["NOTIFIER"].publish("testdone")

    check_process()  # Start monitoring the traceroute process

def _not_implemented(*args):
    """ This function is not implemented """
    raise RuntimeError("plugin functionality not implemented")

def neubot_plugin_spec():
    """ Returns the traceroute plugin's spec """
    return {
        "spec_version": 1.0,
        "name": "traceroute",
        "short_description": "Neubot traceroute module",
        "author": "Simone Basso <bassosimone@gmail.com>",
        "version": 1.0,

        "test_controller": {
            "spec_version": 1.0,
            "client": {
                "run": _run_traceroute,
                "params": {
                    "address": str,
                    "timeout": float
                },
            },
            "server": {
                "run": _not_implemented,
                "params": {
                },
            }
        },

        # Basically this is an alias for `test_controller`
        "test_provider": {
            "spec_version": 1.0,
            "client": {
                "run": _run_traceroute,
                "params": {
                    "address": str,
                    "timeout": float
                },
            },
            "server": {
                "run": _not_implemented,
                "params": {
                },
            }
        },

        "backend": {
            "spec_version": 2.0,
        }
    }
