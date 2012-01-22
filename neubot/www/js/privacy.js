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
    window.location.reload();
    return false;
}

function setPrivacyError(jqXHR, textStatus, errorThrown) {
    alert(jqXHR.statusText + "\nNo setting saved");
    window.location.reload();
    return False;
}

function setPrivacy() {
    //
    // Set explicitly values to '1' or '0' because it is confusing
    // for the user to see boolean values represented both as numbers
    // and as 'true' or 'false' in ``settings.html``.
    //
    utils.setConfigVars({
        'privacy.informed':
          jQuery("#check_privacy_informed").attr("checked") ? "1" : "0",
        'privacy.can_collect':
          jQuery("#check_privacy_can_collect").attr("checked") ? "1" : "0",
        'privacy.can_publish':
          jQuery("#check_privacy_can_publish").attr("checked") ? "1" : "0"
      },
      setPrivacySuccess,
      setPrivacyError
    );
    return false;
}

function checkPrivacy(data) {
    var hidden = true;

    if (data['privacy.informed']) {
        jQuery("#check_privacy_informed").attr("checked", "checked");
    }
    else {
        hidden = false;
    }
    if (data['privacy.can_collect']) {
        jQuery("#check_privacy_can_collect").attr("checked", "checked");
    }
    else {
        hidden = false;
    }
    if (data['privacy.can_publish']) {
        jQuery("#check_privacy_can_publish").attr("checked", "checked");
    }
    else {
        hidden = false;
    }

    // Unhide text that prompts users to provide privacy permissions
    if (!hidden) {
        jQuery('#privacy_not_ok').css('display', 'block');
    }

    return false;
}

function privacy_init() {
    utils.setActiveTab("privacy");

    utils.getConfigVars(checkPrivacy);

    tracker = state.tracker();
    tracker.start();
};

jQuery(document).ready(function() {
    i18n.translate(privacy_init);
});
