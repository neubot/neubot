/* neubot/www/js/privacy.js */
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

function setPrivacySuccess() {
    alert("Privacy settings successfully saved");
    return false;
}

function setPrivacyError(jqXHR, textStatus, errorThrown) {
    alert(jqXHR.statusText + "\nNo setting saved");
    return False;
}

function setPrivacy() {
    setConfigVars({
        'privacy.informed': jQuery("#check_privacy_informed").attr("checked"),
        'privacy.can_collect': jQuery("#check_privacy_can_collect").attr("checked"),
        'privacy.can_share': jQuery("#check_privacy_can_share").attr("checked")
      },
      setPrivacySuccess,
      setPrivacyError
    );
    return false;
}

function checkPrivacy(data) {
    if (data['privacy.informed']) {
        jQuery("#check_privacy_informed").attr("checked", "checked");
    }
    if (data['privacy.can_collect']) {
        jQuery("#check_privacy_can_collect").attr("checked", "checked");
    }
    if (data['privacy.can_share']) {
        jQuery("#check_privacy_can_share").attr("checked", "checked");
    }
    return false;
}

jQuery(document).ready(function() {
    utils.setActiveTab("privacy");

    getConfigVars(checkPrivacy);

    tracker = state.tracker();
    tracker.start();
});
