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

import smtplib
import hashlib


def sendmail(smarthost, local_hostname, sha256_fpr, sender, recipients,
             message):
    smtp = smtplib.SMTP(smarthost, local_hostname=local_hostname)
    smtp.starttls()
    server_certificate = smtp.sock.getpeercert(True)

    sha256_fpr = sha256_fpr.replace(":", "").lower()
    if hashlib.sha256(server_certificate).hexdigest().lower() != sha256_fpr:
        raise RuntimeError("Bad server certificate")

    try:
        smtp.sendmail(sender, recipients, message)
    except:
        # FIXME: Handle exception
        raise
    return True


if __name__ == "__main__":
    import sys

    smarthost, local_hostname, sha256_fpr, sender, recipient, \
        message = sys.argv[1:]
    sendmail(smarthost, local_hostname, sha256_fpr, sender,
             [recipient], message)
