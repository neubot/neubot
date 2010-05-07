# Makefile
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
# Makefile
#

ARCHIVE = neubot
.PHONY: _all _archives clean help install uninstall

_all: help

_archives:
	@echo "[ARCHIVES] $(ARCHIVE).tar.gz $(ARCHIVE).zip"
	@git archive --format=tar --prefix=$(ARCHIVE)/ HEAD > $(ARCHIVE).tar
	@gzip -9 $(ARCHIVE).tar
	@git archive --format=zip --prefix=$(ARCHIVE)/ HEAD > $(ARCHIVE).zip
clean:
	@echo "[CLEAN]"
	@find . -type f -name \*.pyc -exec rm {} \;
	@rm -rf -- build/ dist/ $(ARCHIVE).tar.* $(ARCHIVE).zip
help:
	@echo "[HELP] Available targets"
	@cat Makefile|grep '^[a-zA-Z]*:'|sed 's/:.*$$//'|sed 's/^/\t/'
install:
	@echo "[INSTALL] Create directory /usr/share/neubot"
	@if [ -e /usr/share/neubot ]; then				\
	    echo "error: /usr/share/neubot already exists.";		\
	    exit 1;							\
	fi
	@for DIR in / /http /network /testing; do			\
	    DIR=/usr/share/neubot$$DIR;					\
	    install -d $$DIR;						\
	    if [ $$? -ne 0 ]; then					\
	        exit 1;							\
	    fi;								\
	done
	@echo "[INSTALL] Install sources at /usr/share/neubot"
	@PyFiles=`find neubot -type f -name \*.py`;			\
	 for PyFile in $$PyFiles; do					\
	    install -m644 $$PyFile /usr/share/$$PyFile;			\
	    if [ $$? -ne 0 ]; then					\
	        exit 1;							\
	    fi;								\
	 done
	@echo "[INSTALL] Byte-compile sources at /usr/share/neubot"
	@python -m compileall -q /usr/share/neubot
	@echo "[INSTALL] Install /usr/bin/neubot"
	@install bin/neubot /usr/bin
	@echo "[INSTALL] Create directory /var/run/neubot"
	@install -d /var/run/neubot
	@echo "[INSTALL] Creating group _neubot"
	@groupadd _neubot
	@echo "[INSTALL] Creating user _neubot"
	@useradd -d /var/run/neubot -g _neubot -s /bin/false _neubot
	@if [ -f /etc/lsb-release ]; then				\
	    . /etc/lsb-release;						\
	    if [ "$$DISTRIB_ID" = "Ubuntu" ]; then			\
	        echo "[INSTALL] Install /etc/init.d/neubot";		\
	        install etc/init.d/neubot /etc/init.d/neubot;		\
	        for N in 2 3 4 5; do					\
	            echo "[INSTALL] Symlink /etc/rc$${N}.d/S98neubot";	\
	            ln -s /etc/init.d/neubot /etc/rc$${N}.d/S98neubot;	\
	        done;							\
	        echo "[INSTALL] Symlink /etc/rc6.d/K08neubot";		\
	        ln -s /etc/init.d/neubot /etc/rc6.d/K08neubot;		\
	        echo "[INSTALL] Starting neubot";			\
	        /etc/init.d/neubot start;				\
	    fi;								\
	fi
uninstall:
	@if [ -f /etc/lsb-release ]; then				\
	    . /etc/lsb-release;						\
	    if [ "$$DISTRIB_ID" = "Ubuntu" ]; then			\
	        echo "[UNINSTALL] Stop the running neubots";		\
	        /etc/init.d/neubot stop;				\
	        for N in 2 3 4 5; do					\
	            echo "[UNINSTALL] Remove /etc/rc$${N}.d/S98neubot";	\
	            rm -rf /etc/rc$${N}.d/S98neubot;			\
	        done;							\
	        echo "[UNINSTALL] Remove /etc/rc6.d/K08neubot";		\
	        rm -rf /etc/rc6.d/K08neubot;				\
	        echo "[UNINSTALL] Remove /etc/init.d/neubot";		\
	        rm -rf /etc/init.d/neubot;				\
	    fi;								\
	fi
	@echo "[UNINSTALL] Remove directory /usr/share/neubot"
	@rm -rf /usr/share/neubot
	@echo "[UNINSTALL] Remove file /usr/bin/neubot"
	@rm -rf /usr/bin/neubot
	@echo "[UNINSTALL] Remove directory /var/run/neubot"
	@rm -rf /var/run/neubot
	@echo "[UNINSTALL] Remove user _neubot"
	@userdel _neubot
	@echo "[UNINSTALL] Remove group _neubot"
	@groupdel _neubot || true
