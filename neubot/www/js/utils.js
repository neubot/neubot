/* neubot/www/utils.js */
/*
 * Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>,
 *  Universita` degli Studi di Milano
 * Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
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

var utils = (function() {
    var self = {};

    self.toMs = function(x) {
        return (1000 * x).toFixed(0) + " ms";
    }

    self.toMsNumber = function(x) {
        return (1000 * x);
    }

    self.toMbitsPerSecondNumber = function(x) {
        return (x * 8 / 1000 / 1000);
    }

    self.toMbitsPerSecond = function(x) {
        return (x * 8 / 1000 / 1000).toFixed(3) + " Mbit/s";
    }

    self.toFixed = function(x) {
        return x.toFixed(3);
    }

    self.getText = function(text) {
        if (text == "")
            return (text);
        text = jQuery.trim(text);
        return (text);
    }

    self.getNumber = function(text) {
        if (text == "") {
            return (text);
        }
        var number = Number(text);
        return (number);
    }

    self.getNow = function() {
        var date = new Date();
        return date.getTime();
    }

    self.getTimeFromMicroseconds = function(t, convert) {
        t = self.getNumber(t);
        if (!t) {
            t = utils.getNow();
        }
        else {
            t = t / 1000;
        }
        if (convert) {
            t = formatTime(t);
        }
        return t;
    }

    self.getTimeFromSeconds = function(t, convert, seconds) {
        t = self.getNumber(t);
        if (!t) {
            t = utils.getNow();
        }
        else {
            t *= 1000;
        }
        if (convert) {
            t = utils.formatDateTime(t, seconds);
        }
        return t;
    }

    self.formatMinutes = function(t) {
        t = t / 1000;
        tm = Math.ceil(t / 60);

        // Change t to tm to differentiate from timestamp
        if (tm > 1) {
            s = tm + " minutes";
        }
        else {
            s = "less than one minute";
        }
        return (s);
    }

    self.strPad = function(n) {
        return n < 10 ? '0' + n : n
    }

    self.formatDateTime = function(t, seconds) {
        var date = new Date(t);
        var myret = date.getFullYear() + '-' + self.strPad(date.getMonth() + 1)
          + '-' + self.strPad(date.getDate()) + '\n'
          + self.strPad(date.getHours()) + ':'
          + self.strPad(date.getMinutes());
        if (seconds) {
            myret += ':' + self.strPad(date.getSeconds());
        }
        return myret;
    }

    self.setActiveTab = function(tabname) {
        jQuery("#menu_tab_list li").removeClass("active");
        jQuery("#tab_" + tabname).addClass("active");
        return false;
    }

    self.setStatusLabels = function(data) {
        if (data.enabled == "1") {
            jQuery("#statusBoxSpan").html(i18n.get("enabled"));
            jQuery("#statusBoxSpan").css("color", "#3DA64E");
            jQuery("#statusBoxA").html(i18n.get("Disable"));
            jQuery("#statusBoxA").unbind('click');
            jQuery("#statusBoxA").click(function () {
                self.setConfigVars({'enabled': 0});
            });
        }
        else {
            jQuery("#statusBoxSpan").html(i18n.get("disabled"));
            jQuery("#statusBoxSpan").css("color", "#c00");
            jQuery("#statusBoxA").html(i18n.get("Enable"));
            jQuery("#statusBoxA").unbind('click');
            jQuery("#statusBoxA").click(function () {
                self.setConfigVars({'enabled': 1});
            });
        }
    }

    self.getConfigVars = function(myfunction) {
        return self.getSetConfigVars(myfunction);
    }

    self.setConfigVars = function(value, success, error) {
        return self.getSetConfigVars(success, true, value, error);
    }

    self.getSetConfigVars = function(myfunction, change, value, myerror) {
        var data = {};
        var type = "GET";
        var success = undefined;
        var error = undefined;

        if (change) {
            data = value;
            type = "POST";
        }

        if (myfunction) {
            success = function(data) {
                myfunction(data);
            }
        }

        if (myerror) {
            error = function(jqXHR, textStatus, errorThrown) {
                myerror(jqXHR, textStatus, errorThrown);
            }
        }

        jQuery.ajax({
            url: '/api/config',
            data: data,
            type: type,
            dataType: 'json',
            success: success,
            error: error
        });

        return false;
    }

    self.startTest = function() {

        var success = function() {
        };

        var error = function(jqXHR, textStatus, errorThrown) {
            alert("Start test failed: " + jqXHR.statusText);
        };

        jQuery.ajax({
            url: '/api/runner',
            data: {test: jQuery('#select_startnow').val()},
            type: 'GET',
            dataType: 'json',
            success: success,
            error: error
        });
    }

    return self;
})();
