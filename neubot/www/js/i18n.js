/* neubot/www/js/i18n.js */
/*-
 * Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>,
 *  Universita' degli Studi di Milano
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

var LANG = {};

var i18n = {
    languages: {
        it: 'Italian'
    },

    get: function(label) {
        if (LANG[label]) {
            return LANG[label];
        }
        else {
            return label;
        }
    },

    getLanguageInUse: function() {
        var lang = undefined;
        jQuery.ajax({
            url: '/api/config',
            data: {},
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                lang = data['www.lang'];
            },
            async: false
        });
        if (!lang || lang == 'default') {
            if (navigator.userLanguage) {
                lang = navigator.userLanguage.toLowerCase();
            }
            else if (navigator.language) {
                lang = navigator.language.toLowerCase();
            }
        }
        return lang;
    },

    translate_page: function(data, patt) {
        jQuery(".i18n").each(function(index, element) {
            var classList = jQuery(element).attr('class').split(/\s+/);
            jQuery.each(classList, function(i, v) {
                if ((result = patt.exec(v)) && LANG[result[1]]) {
                    switch (element.tagName.toLowerCase()) {
                    case "textarea":
                        jQuery(element).text(LANG[result[1]]);
                        break;
                    default:
                        jQuery(element).html(LANG[result[1]]);
                        break;
                    }
                }
            });
        });
    },

    translate: function(init_caller) {
        var lang = this.getLanguageInUse();
        if (!lang || !this.languages[lang]) {
            jQuery(".i18n").css("visibility", "visible");
            init_caller();
            return;
        }

        jQuery.ajax({
            url: "lang/" + lang + ".js",
            dataType: 'script',
            context: this,
            success: function(data) {
                this.translate_page(data, /^(i18n_.*)$/i);
                jQuery(".i18n").css("visibility", "visible");
                init_caller();
            }
        });
    }
};
