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
import glob
import logging
import os
import SocketServer
import tempfile

try:
    import simplejson as json
except ImportError:
    import json

from encryptmail.common import setup_logging, Mail
from encryptmail.encrypt import encrypt_mail
from encryptmail.smtp import sendmail


log = logging.getLogger(__name__)


class EncryptMTA(SocketServer.StreamRequestHandler):
    def handle(self):
        try:
            mailinfo = json.load(self.rfile)
        except json.JSONDecodeError as e:
            log.error("Error decoding JSON: %s", e, exc_info=True)
            return False

        spoolname = ""
        with tempfile.NamedTemporaryFile(prefix="mail-",
                                         dir=self.server.spooldir,
                                         delete=False) as spoolfile:
            spoolfile.write(json.dumps(mailinfo))
            spoolname = spoolfile.name
        log.info("Mail spooled as %s", spoolname)


def start(server_address, spooldir,
          smarthost, local_hostname, sha256_fpr, sender,  # sendmail args
          gpgrecipients, contingencydir, gpghomedir,  # encrypt_mail args
          force_recipients=None, force_gpgrecipients=None,
          ):
    try:
        os.unlink(server_address)
    except OSError:
        if os.path.exists(server_address):
            raise

    # strict umask for spooled mails
    os.umask(0077)
    jsonserver = SocketServer.UnixStreamServer(server_address, EncryptMTA)
    os.chmod(server_address, 0777)

    logging.info("Server started at %s", server_address)
    # FIXME: Should be a config option
    jsonserver.timeout = 3600
    jsonserver.spooldir = spooldir

    def checkspool():
        for mailfile in glob.glob(os.path.join(spooldir, "*")):
            with open(mailfile) as ifile:
                try:
                    mail = Mail(json_=ifile.read())
                except:
                    log.error("Error reading mail %s", mailfile, exc_info=True)
                    continue

            encryptedmessage = encrypt_mail(mail.message, gpgrecipients,
                                            contingencydir, gpghomedir)
            if force_recipients is not None:
                recipients = force_recipients
                log.info("Mail recipients rewritten from '%r' to '%s'",
                         mail.recipients, recipients)
            elif force_gpgrecipients is not None:
                recipients = gpgrecipients
                log.info("Mail recipients rewritten from '%r' to gpg "
                         "recipients '%s'", mail.recipients, recipients)
            else:
                recipients = mail.recipients
            try:
                sendmail(smarthost, local_hostname, sha256_fpr, sender,
                         recipients, encryptedmessage)
                os.unlink(mailfile)
                log.info("Sent spooled mail %s to %s", mailfile,
                         recipients)
            except:
                log.error("Error sending mail %s", mailfile, exc_info=True)

    checkspool()
    while True:
        jsonserver.handle_request()
        checkspool()


if __name__ == "__main__":
    setup_logging()
    server_address = "encryptmail.sock"
    spooldir = os.path.abspath("spool")
    import sys
    smarthost, local_hostname, sha256_fpr, sender, \
        gpgrecipients, contingencydir, gpghomedir = sys.argv[1:]

    start(server_address, spooldir,
          smarthost, local_hostname, sha256_fpr, sender,
          gpgrecipients, contingencydir, gpghomedir)
