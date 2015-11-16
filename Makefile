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
prefix=/usr/local
bindir=$(prefix)/bin
sysconfdir=/etc

basedir=/var/lib/encryptmail
spooldir=/var/spool/encryptmail
sockdir=/var/run/encryptmail
gpghomedir=$(basedir)/.gnupg
contingencydir=$(basedir)/unencrypted_mails
unitdir=$(prefix)/lib/systemd/system
tmpfiles.d=$(prefix)/lib/tmpfiles.d

install:
	#install -D -p -m 755 encryptmail.py $(DESTDIR)$(bindir)/encryptmail
	install -d -m 700 $(DESTDIR)$(basedir)
	install -d -m 700 $(DESTDIR)$(gpghomedir)
	install -d -m 700 $(DESTDIR)$(contingencydir)
	install -d -m 755 $(DESTDIR)$(sysconfdir)/encryptmail
	install -d -m 700 $(DESTDIR)$(spooldir)
	install -d -m 755 $(DESTDIR)$(sockdir)
	install -D -p -m 644 encryptmail.yaml $(DESTDIR)$(sysconfdir)/encryptmail/encryptmail.yaml
	install -D -p -m 644 encryptmail.service $(DESTDIR)$(unitdir)/encryptmail.service
	install -D -p -m 644 encryptmail-tmpfile.conf $(DESTDIR)$(tmpfiles.d)/encryptmail.conf
