/* libneubot/poller.h */

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

struct NeubotPollable;
struct NeubotPoller;

typedef void (neubot_pollable_handler)(void *);
typedef void (neubot_poller_callback)(void *);

/*
 * NeubotPoller API
 */

struct NeubotPoller *neubot_poller_construct(void);

int neubot_poller_sched(struct NeubotPoller *, double,
    neubot_poller_callback *, void *);

void neubot_poller_loop(struct NeubotPoller *);

void neubot_poller_break_loop(struct NeubotPoller *);

/*
 * NeubotPollable API
 */

struct NeubotPollable *neubot_pollable_construct(struct NeubotPoller *,
    neubot_pollable_handler *, neubot_pollable_handler *,
    neubot_pollable_handler *, void *);

int neubot_pollable_attach(struct NeubotPollable *, long long);

void neubot_pollable_detach(struct NeubotPollable *);

long long neubot_pollable_fileno(struct NeubotPollable *);

int neubot_pollable_set_readable(struct NeubotPollable *);

int neubot_pollable_unset_readable(struct NeubotPollable *);

int neubot_pollable_set_writable(struct NeubotPollable *);

int neubot_pollable_unset_writable(struct NeubotPollable *);

void neubot_pollable_set_timeout(struct NeubotPollable *, double timeout);

void neubot_pollable_clear_timeout(struct NeubotPollable *);

void neubot_pollable_close(struct NeubotPollable *);
