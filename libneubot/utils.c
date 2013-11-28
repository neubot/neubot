/* libneubot/utils.c */

/*-
 * Copyright (c) 2013
 *     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
 *     and Simone Basso <bassosimone@gmail.com>
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

#include <sys/time.h>

#include <string.h>

#include "utils.h"

void
neubot_timeval_now(struct timeval *tv)
{
        (void)gettimeofday(tv, NULL);
}

double
neubot_time_now(void)
{
        struct timeval tv;
        double result;

        (void)gettimeofday(&tv, NULL);
        result = tv.tv_sec + tv.tv_usec / (double)1000000.0;

        return (result);
}
