/*-
 * win32/neubot-start.c
 * Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
 *   NEXA Center for Internet & Society at Politecnico di Torino
 *
 * This file is part of Neubot <http://www.neubot.org/>.
 *
 * Neubot is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Neubot is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * Wrapper for neubot that invokes "neubot.exe start" which will
 * ensure that the daemon is running in background.
 */

#define NEUBOT_CMDLINE "neubot.exe start"
#include "neubot-exec.h"
