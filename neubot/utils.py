# neubot/utils.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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

import json
import logging
import logging.handlers
import traceback

def prettyprint_exception(write=logging.error, eol=""):
	content = traceback.format_exc()
	for ln in content.splitlines():
		write(ln + eol)

def versioncmp(left, right):
    left = map(int, left.split("."))
    right = map(int, right.split("."))
    for i in range(0, 3):
        diff = left[i] - right[i]
        if diff:
            return diff
    return 0

def prettyprint_json(write, prefix, octets, eol=""):
    obj = json.loads(octets)
    lines = json.dumps(obj, ensure_ascii=True, indent=2)
    for line in lines.splitlines():
        write(prefix + line + eol)
