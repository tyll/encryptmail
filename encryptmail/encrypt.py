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


import argparse
import datetime
from email.message import Message
from email.parser import Parser
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.encoders import encode_7or8bit
import logging
import os
import subprocess
import sys
import tempfile

from encryptmail.config import global_config
from encryptmail.common import setup_logging

log = logging.getLogger(__name__)


def copy_headers(orig, new_outer):
    good_headers = ("From", "To", "Subject")

    bad_headers = ("Transfer-Encoding", "Content-Type")
    for header, value in orig.items():
        if header in good_headers or \
                header not in bad_headers:
            new_outer[header] = value
    return new_outer


def encrypt_mail(inmail, recipients, contingencydir, gpghomedir=None):
    parser = Parser()
    if hasattr(inmail, "read"):
        orig = parser.parse(inmail)
    else:
        orig = parser.parsestr(inmail)
    contingencydir = os.path.expanduser(contingencydir)
    if gpghomedir:
        gpghomedir = os.path.expanduser(gpghomedir)
    if isinstance(recipients, str):
        recipients = [recipients]

    # minimal message with data to be encrypted
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

    if recipients:
        gpg_command = ["gpg"]
        if gpghomedir:
            gpg_command.extend(["--homedir", gpghomedir])
        gpg_command.extend(["--batch", "--quiet", "--no-secmem-warning",
                            "--no-tty",
                            "--trust-model", "always",
                            "--armor", "--output", "-", "--encrypt"])

        for r in recipients:
            gpg_command.append("-r")
            gpg_command.append(r)

        popen = subprocess.Popen(gpg_command,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        encrypted, errors = popen.communicate(input=str(new))
        status = popen.returncode
    else:
        status = "invalid"
        errors = "No recipients set"

    if status == 0 and "-----BEGIN PGP MESSAGE-----" in encrypted:
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
        now = datetime.datetime.now()
        ofilename = "encryptmail-" + str(now) + "-unencrypted.eml"
        localcopy = os.path.join(contingencydir, ofilename)
        try:
            fd = os.open(localcopy, os.O_WRONLY | os.O_CREAT, 0600)
            out = os.fdopen(fd, "wb")
            out.write(str(orig))
            out.close()
        except:
            log.error("Storing unencrypted message", exc_info=True)
            try:
                with tempfile.NamedTemporaryFile(
                        prefix="encryptmail-",
                        suffix="-unencrypted.eml") as out:
                    out.write(str(orig))
                    localcopy = out.name
            except:
                log.error("Storing unencrypted message in tempdir",
                          exc_info=True)
                localcopy = "nowhere (too many exceptions)"

        message = """{sep}
gpg encryption failed with exit status {status}

{errors}

A local copy of the e-mail was stored at {localcopy}
{sep}""".format(status=status, errors=errors,
                localcopy=localcopy, sep="=" * 80)
        new_outer = MIMEText(message)

    new_outer = copy_headers(orig, new_outer)
    return new_outer.as_string()


if __name__ == "__main__":
    firstparser = argparse.ArgumentParser(add_help=False)

    # parse this argument first to be able to load config file for defaults
    firstparser.add_argument("-c", "--configfile",
                             help="Path to configuration file", metavar="FILE")

    args, unparsed = firstparser.parse_known_args()
    if args.configfile:
        global_config.update_yaml_file(args.configfile)

    argumentparser = argparse.ArgumentParser(parents=[firstparser])
    argumentparser.set_defaults(**global_config.encryption_config)
    argumentparser.add_argument("--recipients",
                                help="comma separated list of recipients")
    argumentparser.add_argument("--gpghomedir",
                                help="GPG homedir, e.g. ~/.gnupg")
    argumentparser.add_argument(
        "--contingencydir",
        help="Dir to store mails in case of encryption failure")
    argumentparser.add_argument("emailfile", nargs="?", default=None)
    args = argumentparser.parse_args()
    setup_logging()

    if args.recipients is None:
        log.error("At least one recipient is required")
        sys.exit(1)
    else:
        recipients = args.recipients.split(",")

    if args.emailfile:
        with open(args.emailfile) as ifile:
            new_mail = encrypt_mail(ifile, recipients, args.contingencydir,
                                    args.gpghomedir)
    else:
        new_mail = encrypt_mail(sys.stdin, recipients, args.contingencydir,
                                args.gpghomedir)
    sys.stdout.write(new_mail)
