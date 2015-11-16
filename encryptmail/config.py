#! /usr/bin/python -tt
# vim: fileencoding=utf8
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
""" :author: Till Maas
    :contact: opensource@till.name
    :license: GPLv2+
"""
__docformat__ = "restructuredtext"

import yaml

DEFAULT_YAML = """
encryption:
    # comma-separated list of recipients
    recipients:

    # Directory to store messages in if encryption fails
    contingencydir: .

    # GnuPG homedir
    gpghomedir: ~/.gnupg
smtp:
    spooldir:
    socket:

# vim: filetype=yaml
"""


class Config(object):
    """ Config management class
    """
    def __init__(self, yaml_file=None, yaml_data=None, config=None,
                 load_default=True):
        self.config = {}

        if load_default:
            self.update_yaml(DEFAULT_YAML)
        if yaml_file:
            self.update_yaml_file(yaml_file)
        elif yaml_data:
            self.update_yaml(yaml_data)
        elif config:
            self.update(config)

        self._encryption_config = {}

    def update_yaml_file(self, new_yaml_file, old=None):
        if not old:
            old = self.config
        file = open(new_yaml_file, "rb")
        new_yaml = file.read()
        file.close()

        old = self.update_yaml(new_yaml, old)
        return old

    def update_yaml(self, new_yaml, old=None):
        if not old:
            old = self.config
        new = yaml.load(new_yaml)
        old = self.update(new, old)
        return old

    def update(self, new, old=None):
        """ Update dictionary with new values recursively.

        :Parameters:
            new : dict
                new dictionary
            old : dict
                old dictionary, defaults to self.config

        """
        if not old:
            old = self.config
        for k, v in new.items():
            if k in old.keys():
                if isinstance(old[k], dict):
                    old[k] = self.update(new[k], old[k])
                else:
                    old[k] = new[k]
            else:
                old[k] = new[k]
        self._encryption_config = {}
        return old

    @property
    def encryption_config(self):
        if not self._encryption_config:
            b = {}
            b.update(self.config["encryption"])
            for c, v in b.items():
                if isinstance(v, str):
                    b[c] = v % b

            self._encryption_config = b
        return self._encryption_config

    @property
    def yaml(self):
        return yaml.dump(self.config, indent=4, default_flow_style=False)

    def __getitem__(self, *args):
        return self.config.__getitem__(*args)

global_config = Config()


if __name__ == '__main__':
    cf = Config()

    print "Default config"
    print(cf.config)
    print "yaml of default config"
    print cf.yaml

    print "Global config"
    print(cf.config)

    print "\nEncryption config"
    print(cf.encryption_config)
