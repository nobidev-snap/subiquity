# Copyright 2018 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import copy
import logging
from typing import Set
from urllib import parse

from curtin.commands.apt_config import (
    get_arch_mirrorconfig,
    get_mirror,
    PRIMARY_ARCHES,
    )
from curtin.config import merge_config

try:
    from curtin.distro import get_architecture
except ImportError:
    from curtin.util import get_architecture

log = logging.getLogger('subiquity.models.mirror')


DEFAULT = {
    "preserve_sources_list": False,
    "primary": [
        {
            "arches": PRIMARY_ARCHES,
            "uri": "http://archive.ubuntu.com/ubuntu",
        },
        {
            "arches": ["default"],
            "uri": "http://ports.ubuntu.com/ubuntu-ports",
        },
        ],
}


def countrify_uri(uri: str, cc: str) -> str:
    """ Return a URL where the host is prefixed with a country code. """
    parsed = parse.urlparse(uri)
    new = parsed._replace(netloc=cc + '.' + parsed.netloc)
    return parse.urlunparse(new)


class MirrorModel(object):

    def __init__(self):
        self.config = copy.deepcopy(DEFAULT)
        self.disabled_components: Set[str] = set()

        self.architecture = get_architecture()
        self.default_mirror = self.get_mirror()

    def load_autoinstall_data(self, data):
        if "disable_components" in data:
            self.disabled_components = set(data.pop("disable_components"))
        merge_config(self.config, data)

    def get_apt_config(self):
        config = copy.deepcopy(self.config)
        config["disable_components"] = sorted(self.disabled_components)
        return config

    def mirror_is_default(self):
        return self.get_mirror() == self.default_mirror

    def set_country(self, cc):
        if not self.mirror_is_default():
            return
        uri = self.get_mirror()
        self.set_mirror(countrify_uri(uri, cc=cc))

    def get_mirror(self):
        return get_mirror(self.config, "primary", self.architecture)

    def set_mirror(self, mirror):
        config = get_arch_mirrorconfig(
            self.config, "primary", self.architecture)
        config["uri"] = mirror

    def disable_components(self, comps, add: bool) -> None:
        """ Add (or remove) a component (e.g., multiverse) from the list of
        disabled components. """
        comps = set(comps)
        if add:
            self.disabled_components |= comps
        else:
            self.disabled_components -= comps

    def render(self):
        return {}
