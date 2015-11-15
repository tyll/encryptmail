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

from email.parser import Parser
import email.utils
import os
import socket
import sys

from encryptmail.common import Mail


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
    read_message = False
    recipients = []
    for arg in sys.argv[1:]:
        if arg == "-t":
            read_message = True
        elif arg == "--":
            pass
        else:
            recipients.append(arg)

    raw_message = ""
    while True:
        line = sys.stdin.readline()
        # read until EOF or until a line containing a single dot is read
        if not line or line == ".\n":
            break
        raw_message += line

    if read_message:
        parser = Parser()
        message = parser.parsestr(raw_message)
        for header in "To", "Cc", "Bcc":
            other_recipients = message.get_all("Resent-" + header, [])
            if not other_recipients:
                other_recipients = message.get_all(header, [])

            raw_addresses = [x[1] for x in email.utils.getaddresses(
                other_recipients)]
            recipients.extend(raw_addresses)
    user = os.environ.get("USER", "unknown")
    hostname = os.environ.get("HOSTNAME", "localhost")
    fromaddr = user + "@" + hostname

    mail = Mail(fromaddr=fromaddr, recipients=recipients, message=raw_message)
    success = connect_and_send(sockaddr, mail.json)
    if success:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sendmail("encryptmail.sock")
