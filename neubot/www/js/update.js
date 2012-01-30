/* neubot/www/js/update.js */
/*-
 * Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
 *  NEXA Center for Internet & Society at Politecnico di Torino
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
 * I would like to implement automatic updates under Windows as
 * soon as possible.  However this is not feasible for the upcoming
 * 0.4.4 release.  So here's a webpage that tells users that an
 * updated version is available.  This will hopefully go away before
 * Neubot 0.5.0 (last famous words...).
 */

function update_init() {
    tracker = state.tracker();
    tracker.start();
};

jQuery(document).ready(function() {
    i18n.translate(update_init);
});
