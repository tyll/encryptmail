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

from distutils.core import setup

setup(name="encryptmail",
      description="GPG encrypt e-mails",
      version="0",
      license="GPLv2+",
      author="Till Maas",
      author_email="opensource@till.name",
      url="https://github.com/tyll/encryptmail",
      packages=["encryptmail"],
      scripts=["encryptmail-sendmail", "encryptmail-mta"],
      )
