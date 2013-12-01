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
#include <math.h>

#include <event2/event.h>

#include "log.h"
#include "libneubot.h"
#include "utils.h"

struct NeubotPollable {
        TAILQ_ENTRY(NeubotPollable) entry;
        NeubotPollable_callback handle_close;
        NeubotPollable_callback handle_read;
        NeubotPollable_callback handle_write;
        evutil_socket_t fileno;
        struct NeubotPoller *poller;
        double timeout;
        struct event *evread;
        struct event *evwrite;
        void *opaque;
};

struct NeubotPoller {
        struct event_base *evbase;
        TAILQ_HEAD(, NeubotPollable) head;
};

struct CallbackContext {
        NeubotPoller_callback callback;
        void *opaque;
};

/*
 * NeubotPoller implementation
 */

static void
NeubotPoller_dispatch(evutil_socket_t filenum, short event, void *opaque)
{
        struct NeubotPollable *pollable;

        pollable = (struct NeubotPollable *) opaque;

        if (event & EV_READ)
                pollable->handle_read(pollable->opaque);
        else if (event & EV_WRITE)
                pollable->handle_write(pollable->opaque);
        else
                /* nothing */ ;
}

static inline struct event *
NeubotPoller_event_new(struct NeubotPoller *self, evutil_socket_t filenum,
    short event, void *opaque)
{
        return (event_new(self->evbase, filenum, event,
            NeubotPoller_dispatch, opaque));
}

static inline void
NeubotPoller_register_pollable(struct NeubotPoller *self,
    struct NeubotPollable *pollable)
{
        TAILQ_INSERT_TAIL(&self->head, pollable, entry);
}

static inline void
NeubotPoller_unregister_pollable(struct NeubotPoller *self,
    struct NeubotPollable *pollable)
{
        TAILQ_REMOVE(&self->head, pollable, entry);
}

static void
NeubotPoller_periodic(void *opaque)
{
        struct NeubotPoller *self;
        struct NeubotPollable *pollable;
        struct NeubotPollable *tmp;
        double curtime;
        int retval;

        self = (struct NeubotPoller *) opaque;
        retval = NeubotPoller_sched(self, 10.0,
            NeubotPoller_periodic, self);
        if (retval < 0)
                abort();  /* XXX */

        curtime = neubot_time_now();

        pollable = TAILQ_FIRST(&self->head);
        while (pollable != NULL) {
                if (pollable->timeout >= 0 && curtime > pollable->timeout) {
                        neubot_warn("poller.c: watchdog timeout");
                        tmp = pollable;
                        pollable = TAILQ_NEXT(pollable, entry);
                        NeubotPollable_close(tmp);
                } else
                        pollable = TAILQ_NEXT(pollable, entry);
        }
}

struct NeubotPoller *
NeubotPoller_construct(void)
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

        retval = NeubotPoller_sched(self, 10.0,
            NeubotPoller_periodic, self);
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

static void
NeubotPoller_callfunc(evutil_socket_t fileno, short event, void *opaque)
{
        NeubotPoller_callback callback;
        struct CallbackContext *context;

        context = (struct CallbackContext *) opaque;
        callback = context->callback;
        opaque = context->opaque;

        free(context);

        callback(opaque);
}

int
NeubotPoller_sched(struct NeubotPoller *self, double delta,
    NeubotPoller_callback callback, void *opaque)
{
        struct CallbackContext *context;
        struct timeval tvdelta;
        struct timeval tvnow;
        struct timeval tvresult;

        context = calloc(1, sizeof (*context));
        if (context == NULL)
            return (-1);

        neubot_timeval_now(&tvnow);
        tvdelta.tv_sec = (time_t) floor(delta);
        tvdelta.tv_usec = (suseconds_t) ((delta - floor(delta)) * 1000000);
        evutil_timeradd(&tvnow, &tvdelta, &tvresult);

        context->callback = callback;
        context->opaque = opaque;

        return (event_base_once(self->evbase, -1, EV_TIMEOUT,
          NeubotPoller_callfunc, context, &tvresult));
}

void
NeubotPoller_loop(struct NeubotPoller *self)
{
        event_base_dispatch(self->evbase);
}

void
NeubotPoller_break_loop(struct NeubotPoller *self)
{
        event_base_loopbreak(self->evbase);
}

/*
 * NeubotPollable implementation
 */

static void
NeubotPollable_noop(void *opaque)
{
        /* nothing */ ;
}

struct NeubotPollable *
NeubotPollable_construct(struct NeubotPoller *poller,
    NeubotPollable_callback handle_read,
    NeubotPollable_callback handle_write,
    NeubotPollable_callback handle_close,
    void *opaque)
{
        struct NeubotPollable *self;

        if (handle_read == NULL)
                handle_read = NeubotPollable_noop;
        if (handle_write == NULL)
                handle_write = NeubotPollable_noop;
        if (handle_close == NULL)
                handle_close = NeubotPollable_noop;

        self = calloc(1, sizeof (*self));
        if (self == NULL)
                return (NULL);

        self->poller = poller;
        self->handle_close = handle_close;
        self->handle_read = handle_read;
        self->handle_write = handle_write;
        self->fileno = -1;
        self->opaque = opaque;

        return (self);
}

int
NeubotPollable_attach(struct NeubotPollable *self, long long fileno)
{
        if (self->fileno != -1)
                return (-1);
        /*
         * Note: `long long` simplifies the interaction with SWIG and
         * shall be wide enough to hold evutil_socket_t, which is `int`
         * on Unix and `uintptr_t` on Windows.
         */
        self->fileno = (evutil_socket_t) fileno;
        self->evread = NeubotPoller_event_new(self->poller,
            self->fileno, EV_READ|EV_PERSIST, self);
        if (self->evread == NULL)
                return (-1);
        self->evwrite = NeubotPoller_event_new(self->poller,
            self->fileno, EV_WRITE|EV_PERSIST, self);
        if (self->evwrite == NULL)
                return (-1);
        NeubotPoller_register_pollable(self->poller, self);
        return (0);
}

void
NeubotPollable_detach(struct NeubotPollable *self)
{
        if (self->evread != NULL)
                event_free(self->evread);
        if (self->evwrite != NULL)
                event_free(self->evwrite);

        if (self->fileno != -1) {
                NeubotPoller_unregister_pollable(self->poller, self);
                self->fileno = -1;
        }
}

long long
NeubotPollable_fileno(struct NeubotPollable *self)
{
        return ((long long) self->fileno);
}

int
NeubotPollable_set_readable(struct NeubotPollable *self)
{
        if (self->fileno == -1)
                return (-1);
        return (event_add(self->evread, NULL));
}

int
NeubotPollable_unset_readable(struct NeubotPollable *self)
{
        if (self->fileno == -1)
                return (-1);
        return (event_del(self->evread));
}

int
NeubotPollable_set_writable(struct NeubotPollable *self)
{
        if (self->fileno == -1)
                return (-1);
        return (event_add(self->evwrite, NULL));
}

int
NeubotPollable_unset_writable(struct NeubotPollable *self)
{
        if (self->fileno == -1)
                return (-1);
        return (event_del(self->evwrite));
}

void
NeubotPollable_set_timeout(struct NeubotPollable *self, double timeout)
{
        self->timeout = neubot_time_now() + timeout;
}

void
NeubotPollable_clear_timeout(struct NeubotPollable *self)
{
        self->timeout = -1.0;
}

void
NeubotPollable_close(struct NeubotPollable *self)
{
        NeubotPollable_detach(self);
        self->handle_close(self->opaque);
}
