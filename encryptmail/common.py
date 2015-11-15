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
            self.fromaddr = parsed["fromaddr"]
            self.recipients = parsed["recipients"]
            self.message = parsed["message"]

    @property
    def json(self):
        maildata = dict(fromaddr=self.fromaddr,
                        recipients=self.recipients,
                        message=self.message)
        return json.dumps(maildata)


def setup_logging(logger=logging.getLogger(), level=logging.DEBUG):
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
