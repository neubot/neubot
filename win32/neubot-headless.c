/*-
 * win32/neubot-headless.c
 * Copyright (c) 2010 NEXA Center for Internet & Society
 *
 * This file is part of Neubot.
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
 * Wrapper for neubot that invokes neubot.exe without arguments,
 * thus causing neubot.exe to ensure that the neubot daemon is
 * running in background and then to start a browser instance that
 * points to neubot web interface.
 */

#define NEUBOT_CMDLINE "neubot.exe"
#include "neubot-exec.h"
