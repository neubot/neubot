/* libneubot/poller.c */

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

#include <sys/queue.h>

#include <stdlib.h>

#include <event2/event.h>

#include "log.h"
#include "poller.h"
#include "utils.h"

struct NeubotPollable {
        TAILQ_ENTRY(NeubotPollable) entry;
        neubot_pollable_handler *handle_close;
        neubot_pollable_handler *handle_read;
        neubot_pollable_handler *handle_write;
        evutil_socket_t fileno;
        struct NeubotPoller *poller;
        double timeout;
        struct event *evread;
        struct event *evwrite;
};

struct NeubotPoller {
        struct event_base *evbase;
        TAILQ_HEAD(, NeubotPollable) head;
};

/*
 * NeubotPoller implementation
 */

static void
neubot_poller_handle_pollable_event_(evutil_socket_t filenum,
    short event, void *opaque)
{
        struct NeubotPollable *pollable;

        pollable = (struct NeubotPollable *) opaque;

        if (event & EV_READ)
                pollable->handle_read(pollable);
        else if (event & EV_WRITE)
                pollable->handle_write(pollable);
        else
                /* nothing */ ;
}

static inline struct event *
neubot_poller_event_new_(struct NeubotPoller *self, evutil_socket_t filenum,
    short event, void *opaque)
{
        return (event_new(self->evbase, filenum, event,
            neubot_poller_handle_pollable_event_, opaque));
}

static inline void
neubot_poller_register_pollable_(struct NeubotPoller *self,
    struct NeubotPollable *pollable)
{
        TAILQ_INSERT_TAIL(&self->head, pollable, entry);
}

static inline void
neubot_poller_unregister_pollable_(struct NeubotPoller *self,
    struct NeubotPollable *pollable)
{
        TAILQ_REMOVE(&self->head, pollable, entry);
}

static void
neubot_poller_periodic_(evutil_socket_t fileno, short event, void *opaque)
{
        struct NeubotPoller *self;
        struct NeubotPollable *pollable;
        struct NeubotPollable *tmp;
        double curtime;
        int retval;

        self = (struct NeubotPoller *) opaque;
        retval = neubot_poller_sched(self, 10.0,
            neubot_poller_periodic_, self);
        if (retval < 0)
                abort();

        curtime = neubot_time_now();

        pollable = TAILQ_FIRST(&self->head);
        while (pollable != NULL) {
                if (pollable->timeout >= 0 && curtime > pollable->timeout) {
                        neubot_warn("poller.c: watchdog timeout");
                        tmp = pollable;
                        pollable = TAILQ_NEXT(pollable, entry);
                        neubot_pollable_close(tmp);
                } else
                        pollable = TAILQ_NEXT(pollable, entry);
        }
}

struct NeubotPoller *
neubot_poller_construct(void)
{
        struct NeubotPoller *self;
        int retval;

        self = (struct NeubotPoller *) calloc(1, sizeof (*self));
        if (self == NULL)
                goto failure;

        self->evbase = event_base_new();
        if (self->evbase == NULL)
                goto failure;

        TAILQ_INIT(&self->head);

        retval = neubot_poller_sched(self, 10.0,
            neubot_poller_periodic_, self);
        if (retval != 0)
            goto failure;

        return (self);

failure:
        if (self != NULL && self->evbase != NULL)
                event_base_free(self->evbase);
        if (self != NULL)
                free(self);
        return (NULL);
}

int
neubot_poller_sched(struct NeubotPoller *self, double delta,
    event_callback_fn func, void *opaque)
{
        struct timeval tv;
        neubot_timeval_now(&tv);
        return (event_base_once(self->evbase, -1,
            EV_TIMEOUT, func, opaque, &tv));
}

void
neubot_poller_loop(struct NeubotPoller *self)
{
        event_base_dispatch(self->evbase);
}

void
neubot_poller_break_loop(struct NeubotPoller *self)
{
        event_base_loopbreak(self->evbase);
}

/*
 * NeubotPollable implementation
 */

static void
neubot_pollable_noop_(struct NeubotPollable *self)
{
        /* nothing */ ;
}

struct NeubotPollable *
neubot_pollable_construct(struct NeubotPoller *poller,
    neubot_pollable_handler *handle_read,
    neubot_pollable_handler *handle_write,
    neubot_pollable_handler *handle_close)
{
        struct NeubotPollable *self;

        if (handle_read == NULL)
                handle_read = neubot_pollable_noop_;
        if (handle_write == NULL)
                handle_write = neubot_pollable_noop_;
        if (handle_close == NULL)
                handle_close = neubot_pollable_noop_;

        self = calloc(1, sizeof (*self));
        if (self == NULL)
                return (NULL);

        self->poller = poller;
        self->handle_close = handle_close;
        self->handle_read = handle_read;
        self->handle_write = handle_write;
        self->fileno = -1;

        return (self);
}

int
neubot_pollable_attach(struct NeubotPollable *self, evutil_socket_t fileno)
{
        if (self->fileno != -1)
                return (-1);
        self->fileno = fileno;
        self->evread = neubot_poller_event_new_(self->poller,
            self->fileno, EV_READ|EV_PERSIST, self);
        if (self->evread == NULL)
                return (-1);
        self->evwrite = neubot_poller_event_new_(self->poller,
            self->fileno, EV_WRITE|EV_PERSIST, self);
        if (self->evwrite == NULL)
                return (-1);
        neubot_poller_register_pollable_(self->poller, self);
        return (0);
}

void
neubot_pollable_detach(struct NeubotPollable *self)
{
        if (self->evread != NULL)
                event_free(self->evread);
        if (self->evwrite != NULL)
                event_free(self->evwrite);

        if (self->fileno != -1) {
                neubot_poller_unregister_pollable_(self->poller, self);
                self->fileno = -1;
        }
}

evutil_socket_t
neubot_pollable_fileno(struct NeubotPollable *self)
{
        return (self->fileno);
}

int
neubot_pollable_set_readable(struct NeubotPollable *self)
{
        if (self->fileno == -1)
                return (-1);
        return (event_add(self->evread, NULL));
}

int
neubot_pollable_unset_readable(struct NeubotPollable *self)
{
        if (self->fileno == -1)
                return (-1);
        return (event_del(self->evread));
}

int
neubot_pollable_set_writable(struct NeubotPollable *self)
{
        if (self->fileno == -1)
                return (-1);
        return (event_add(self->evwrite, NULL));
}

int
neubot_pollable_unset_writable(struct NeubotPollable *self)
{
        if (self->fileno == -1)
                return (-1);
        return (event_del(self->evwrite));
}

void
neubot_pollable_set_timeout(struct NeubotPollable *self, double timeout)
{
        self->timeout = neubot_time_now() + timeout;
}

void
neubot_pollable_clear_timeout(struct NeubotPollable *self)
{
        self->timeout = -1.0;
}

void
neubot_pollable_close(struct NeubotPollable *self)
{
        neubot_pollable_detach(self);
        self->handle_close(self);
}
