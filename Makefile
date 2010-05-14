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
.PHONY: _all _archives _docs _release clean help install uninstall

_all: help

_archives:
	@echo "[ARCHIVES] $(ARCHIVE).tar.gz $(ARCHIVE).zip"
	@git archive --format=tar --prefix=$(ARCHIVE)/ HEAD > $(ARCHIVE).tar
	@gzip -9 $(ARCHIVE).tar
	@git archive --format=zip --prefix=$(ARCHIVE)/ HEAD > $(ARCHIVE).zip
_docs:
	@echo "[DOCS]"
	@cd doc && for DIA in *.dia; do					\
	    dia --filter=png $$DIA;					\
	done
_release:
	@echo "[RELEASE]"
	@V=`git tag|tail -n1` 					&&	\
	ARCHIVENAME=neubot-$$V					&&	\
	git archive --format=tar --prefix=$$ARCHIVENAME/		\
	     HEAD | gzip -9 > $$ARCHIVENAME.tar.gz		&&	\
	git archive --format=zip --prefix=$$ARCHIVENAME/		\
	     HEAD > $$ARCHIVENAME.zip				&&	\
	sha256sum $$ARCHIVENAME.* > SHA256
clean:
	@echo "[CLEAN]"
	@find . -type f -name \*.pyc -exec rm -f {} \;
	@rm -rf -- build/ dist/ $(ARCHIVE).tar.* $(ARCHIVE).zip
help:
	@echo "[HELP] Available targets"
	@cat Makefile|grep '^[a-zA-Z]*:'|sed 's/:.*$$//'|sed 's/^/\t/'
install:
	@echo "[INSTALL] Create directory /usr/share/neubot"
	@if [ -e /usr/share/neubot ]; then				\
	    echo "Oops: /usr/share/neubot already exists.";		\
	    echo "  Hey!  Do you want to re-install Neubot, uh?";	\
	    echo "   (Perhaps you got an updated version)";		\
	    echo "  If so, un-install it first, e.g. type:";		\
	    echo "    make uninstall";					\
	    echo "  Then, try again with:";				\
	    echo "    make install";					\
	    exit 1;							\
	fi
	@for DIR in / /application /http /network /testing; do		\
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
	@install bin/unix/neubot /usr/bin
	@echo "[INSTALL] Create directory /var/run/neubot"
	@install -d /var/run/neubot
	@echo "[INSTALL] Create directory /etc/neubot"
	@install -d /etc/neubot
	@echo "[INSTALL] Install /etc/neubot/config"
	@neubot -qE _writeconfig > /etc/neubot/config
	@chmod 644 /etc/neubot/config
	@echo "[INSTALL] Creating group _neubot"
	@groupadd _neubot
	@echo "[INSTALL] Creating user _neubot"
	@useradd -d /var/run/neubot -g _neubot -s /bin/false _neubot
	@if [ -f /etc/lsb-release ]; then				\
	    . /etc/lsb-release;						\
	    if [ "$$DISTRIB_ID" = "Ubuntu" ]; then			\
	        echo "[INSTALL] Install /etc/init.d/neubot";		\
	        install etc/init.d/neubot /etc/init.d/neubot;		\
	        update-rc.d neubot defaults 99;				\
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
	        echo "[UNINSTALL] Remove /etc/init.d/neubot";		\
	        rm -rf /etc/init.d/neubot;				\
	        update-rc.d neubot remove;				\
	    fi;								\
	fi
	@echo "[UNINSTALL] Remove directory /usr/share/neubot"
	@rm -rf /usr/share/neubot
	@echo "[UNINSTALL] Remove file /usr/bin/neubot"
	@rm -rf /usr/bin/neubot
	@echo "[UNINSTALL] Remove directory /var/run/neubot"
	@rm -rf /var/run/neubot
	@echo "[UNINSTALL] Remove directory /etc/neubot"
	@rm -rf /etc/neubot
	@echo "[UNINSTALL] Remove user _neubot"
	@userdel _neubot
	@echo "[UNINSTALL] Remove group _neubot"
	@groupdel _neubot || true
