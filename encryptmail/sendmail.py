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
from email.parser import Parser
import email.utils
import logging
import os
import socket
import sys

from encryptmail.common import Mail, setup_logging


log = logging.getLogger(__name__)


def connect_and_send(sockaddr, message):
    mailsocket = socket.socket(socket.AF_UNIX)
    mailsocket.connect(sockaddr)

    try:
        mailsocket.sendall(message)
    except Exception as e:
        print "ERROR:", e
        return False
    return True


def sendmail(sockaddr):
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-t", dest="read_message", default=False,
                           action="store_true",
                           help="Add recipients from message headers to "
                                "recipients specified on commandline")
    argparser.add_argument("-oi", "-i", dest="until_dotline",
                           help="Do not treat line consisting of only a "
                           "dot ('.') as end of message",
                           action="store_false", default=True)
    argparser.add_argument("-F", dest="sender_fullname", help="Sender "
                           "fullname, only used if there is no From: header. "
                           "Overrides NAME environment variable.",
                           default=None)
    argparser.add_argument("-f", dest="sender_address", help="Sender "
                           "address.", default=None)

    argparser.add_argument("recipients", nargs="*")
    args, unparsed = argparser.parse_known_args()

    # Options to silenty ignore
    # -o: set short config option
    # search for '[x]' on
    # http://www.sendmail.org/~ca/email/doc8.12/op-sh-5.html#sh-5.6
    # to find config optin 'x'
    # -odi: DeliveryMode: interactively
    # -oem: ErrorMode: mailback, always exit with zero
    for unknown in list(unparsed):
        if unknown.startswith("-od") or unknown.startswith("-oe"):
            unparsed.remove(unknown)
            log.debug("Silently ignored unparsed commandline option: %s",
                      unknown)

    if unparsed:
        log.warn("Unparsed commandline options: %r", unparsed)
        log.warn("Full commandline was: %r", sys.argv[1:])

    raw_message = ""
    while True:
        line = sys.stdin.readline()
        # read until EOF or until a line containing a single dot is read
        if not line or (args.until_dotline and line == ".\n"):
            break
        raw_message += line

    parser = Parser()
    message = parser.parsestr(raw_message)
    if args.read_message:
        for header in "To", "Cc", "Bcc":
            other_recipients = message.get_all("Resent-" + header, [])
            if not other_recipients:
                other_recipients = message.get_all(header, [])

            raw_addresses = [x[1] for x in email.utils.getaddresses(
                other_recipients)]
            args.recipients.extend(raw_addresses)

        del message["Bcc"]

    if not args.recipients:
        log.error("No recipients specified")
        return 1

    if not "Date" in message:
        message.add_header("Date", email.utils.formatdate())

    if args.sender_address is None:
        user = os.environ.get("USER", "unknown")
        hostname = socket.getfqdn()
        fromaddr = user + "@" + hostname
    else:
        fromaddr = args.sender_address

    if not "From" in message:
        if args.sender_fullname is None:
            sender_fullname = os.environ.get("NAME", "")
        else:
            sender_fullname = args.sender_fullname

        message.add_header("From",
                           email.utils.formataddr((sender_fullname, fromaddr)))

    if not "Message-Id" in message:
        message.add_header("Message-Id", email.utils.make_msgid("encryptmail"))

    raw_message = message.as_string()

    mail = Mail(fromaddr=fromaddr, recipients=args.recipients,
                message=raw_message)
    success = connect_and_send(sockaddr, mail.json)
    if success:
        return 0
    else:
        log.error("Error sending mail to daemon")
        return 1


if __name__ == "__main__":
    setup_logging()
    sys.exit(sendmail("encryptmail.sock"))
