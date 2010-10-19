# setup.py
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

#
# Use py2exe to create neubot.exe
#

import distutils.core
import os

if os.name != "posix":
    import py2exe
    distutils.core.setup(name="neubot",
        description="Network neutrality bot",
        license="GPLv3",
        packages=["neubot"],
        package_dir={"neubot" : "."},
        version="0.2.8",
        author="Simone Basso",
        author_email="bassosimone@gmail.com",
        console=[{"script": "bin/neubot"}],
        url="http://www.neubot.org")
