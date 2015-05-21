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

import argparse
import ConfigParser
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
import time

log = logging.getLogger(__name__)


def copy_headers(orig, new_outer):
    good_headers = ("From", "To", "Subject")

    bad_headers = ("Transfer-Encoding", "Content-Type")
    for header, value in orig.items():
        if header in good_headers or \
                header not in bad_headers:
            new_outer[header] = value
    return new_outer


def encrypt_mail(ifile, recipients, contingencydir, gpghomedir=None):
    parser = Parser()
    orig = parser.parse(ifile)

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
        now = datetime.datetime.now()
        ofilename = "encryptmail-" + str(now) + "-unencrypted.eml"
        localcopy = os.path.join(contingencydir, ofilename)
        try:
            fd = os.open(localcopy, os.O_WRONLY | os.O_CREAT)
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


def setup_logging():
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s: %(levelname)s: %(message)s',
    )
    # Log in UTC
    formatter.converter = time.gmtime

    console_logger = logging.StreamHandler()
    console_logger.setLevel(logging.DEBUG)
    console_logger.setFormatter(formatter)
    log.addHandler(console_logger)


if __name__ == "__main__":
    argumentparser = argparse.ArgumentParser()
    argumentparser.add_argument("--recipients", default=None,
                                help="comma separated list of recipients")
    argumentparser.add_argument("--gpghomedir", default=None,
                                help="GPG homedir, e.g. ~/.gnupg")
    argumentparser.add_argument(
        "--contingencydir", default=None,
        help="Dir to store mails in case of encryption failure")
    argumentparser.add_argument("emailfile", nargs="?", default=None)
    args = argumentparser.parse_args()
    setup_logging()

    config = ConfigParser.SafeConfigParser()
    configfile = "encryptmail.conf"
    config.read([configfile + ".sample", configfile])
    if args.recipients:
        recipients = args.recipients.split(",")
    else:
        try:
            recipients = config.get("encryptmail", "recipients").split(" ")
        except ConfigParser.NoOptionError:
            recipients = None

    if args.contingencydir:
        contingencydir = args.contingencydir
    else:
        try:
            contingencydir = config.get("encryptmail", "contingencydir")
        except ConfigParser.NoOptionError:
            contingencydir = "."
    if contingencydir:
        contingencydir = os.path.expanduser(contingencydir)

    if args.gpghomedir:
        gpghomedir = args.gpghomedir
    else:
        try:
            gpghomedir = config.get("encryptmail", "gpghomedir")
        except ConfigParser.NoOptionError:
            gpghomedir = None
    if gpghomedir:
        gpghomedir = os.path.expanduser(gpghomedir)

    if args.emailfile:
        with open(args.emailfile) as ifile:
            new_mail = encrypt_mail(ifile, recipients, contingencydir,
                                    gpghomedir)
    else:
        new_mail = encrypt_mail(sys.stdin, recipients, contingencydir,
                                gpghomedir)
    sys.stdout.write(new_mail)
