#!/usr/bin/python -tt
# vim: fileencoding=utf8
# SPDX-License-Identifier: GPL-2.0+
# {{{ License header: GPLv2+
#    This file is part of encryptmail.
#
#    Encryptmail is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 2 of the License, or
#    (at your option) any later version.
#
#    Encryptmail is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with encryptmail.  If not, see <http://www.gnu.org/licenses/>.
# }}}

import email.utils
import logging
import time
try:
    import simplejson as json
except ImportError:
    import json

log = logging.getLogger(__name__)


class Mail(object):
    def __init__(self, fromaddr=None, recipients=None, message=None,
                 json_=None):
        self.fromaddr = fromaddr
        self.recipients = recipients
        self.message = message

        if json_ is not None:
            parsed = json.loads(json_)
            self.fromaddr = parsed["fromaddr"].encode("latin1")
            self.recipients = [
                x.encode("latin1") for x in parsed["recipients"]]
            self.message = parsed["message"].encode("latin1")

    @property
    def json(self):
        maildata = dict(fromaddr=self.fromaddr.decode("latin1"),
                        recipients=[
                            x.decode("latin1") for x in self.recipients],
                        message=self.message.decode("latin1"))
        return json.dumps(maildata)


console_logger = None
def setup_logging(logger=logging.getLogger(), level=logging.DEBUG):
    global console_logger
    logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s: %(levelname)s: %(message)s',
    )
    # Log in UTC
    formatter.converter = time.gmtime

    console_logger = logging.StreamHandler()
    console_logger.setLevel(level)
    console_logger.setFormatter(formatter)
    logger.addHandler(console_logger)


def set_logging_level(loglevel):
    global console_logger
    loglevel = getattr(logging, loglevel.upper())
    console_logger.setLevel(loglevel)


def fqdnify_headers(message, hostname, headers=("To", "From", "Cc")):
    # make all addresses use FQDNs
    for header in headers:
        fixed_addresses = []
        raw_addresses = message.get_all(header)
        if not raw_addresses:
            continue

        addresses = email.utils.getaddresses(raw_addresses)

        for name, addr in addresses:
            if not "@" in addr:
                addr = addr + "@" + hostname
            fixed_addresses.append(email.utils.formataddr((name, addr)))

        if fixed_addresses:
            del message[header]
            message[header] = ", ".join(fixed_addresses)
