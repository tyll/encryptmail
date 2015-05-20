#!/usr/bin/python -tt
# vim: fileencoding=utf8
# SPDX-License-Identifier: GPL-2.0+
# {{{ License header: GPLv2+
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# }}}

import ConfigParser
from email.message import Message
from email.parser import Parser
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.encoders import encode_7or8bit
import subprocess
import sys


def copy_headers(orig, new_outer):
    good_headers = ("From", "To", "Subject")

    bad_headers = ("Transfer-Encoding", "Content-Type")
    for header, value in orig.items():
        if header in good_headers or \
                header not in bad_headers:
            new_outer[header] = value
    return new_outer


def encrypt_mail(ifile, recipients):
    parser = Parser()
    orig = parser.parse(ifile)

    new = Message()

    keep_headers = ("Content-Type", "Transfer-Encoding", "Content-Disposition")
    for h in keep_headers:
        if h in orig:
            new[h] = orig[h]

    if orig.is_multipart():
        for p in orig.get_payload():
            new.attach(p)
    else:
        new.set_payload(orig.get_payload())

    # maybe set --homedir
    gpg_command = ["gpg", "--batch", "--quiet", "--no-secmem-warning",
                   "--no-tty", "--trust-model", "always", "--armor",
                   "--output", "-", "--encrypt"]

    for r in recipients:
        gpg_command.append("-r")
        gpg_command.append(r)

    popen = subprocess.Popen(gpg_command,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

    encrypted, errors = popen.communicate(input=str(new))
    status = popen.returncode

    if status == 0:
        new_outer = MIMEMultipart("encrypted",
                                  protocol="application/pgp-encrypted")
        new_outer["Transfer-Encoding"] = "7bit"
        new_outer.preamble = "OpenPGP/MIME encrypted message, see "\
            "http://tools.ietf.org/html/rfc3156"

        gpg_attachment = MIMEApplication("Version: 1\n",
                                         _subtype="pgp-encrypted",
                                         _encoder=encode_7or8bit)
        gpg_attachment["Content-Disposition"] = "inline"
        new_outer.attach(gpg_attachment)

        gpg_message = MIMEApplication(encrypted,
                                      _subtype="octet-stream",
                                      _encoder=encode_7or8bit)
        gpg_message["Content-Disposition"] = "inline"
        new_outer.attach(gpg_message)
    else:
        local_copy = "/does/not/exist"
        message = """{sep}
gpg encryption failed with exit status {status}

{errors}

A local copy of the e-mail was stored at {local_copy}
{sep}""".format(status=status, errors=errors,
                local_copy=local_copy, sep="=" * 80)
        new_outer = MIMEText(message)

    new_outer = copy_headers(orig, new_outer)
    return new_outer.as_string()


if __name__ == "__main__":
    config = ConfigParser.SafeConfigParser()
    configfile = "encryptmail.conf"
    config.read([configfile])
    recipients = config.get("encryptmail", "recipients").split(" ")
    new_mail = encrypt_mail(sys.stdin, recipients)
    sys.stdout.write(new_mail)
