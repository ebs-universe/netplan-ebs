# Copyright (c) 2018  StorPool.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
A parser for the netplan configuration.
"""


import itertools
import os
import yaml

from . import config as npconfig
from . import interface as npiface


class ParseFileException(Exception):
    """
    An exception raised while parsing a NetPlan config file.
    """
    def __init__(self, fname, inner):
        """
        Initialize a ParseFileException object with
        the specified filename and inner exception.
        """
        super(ParseFileException, self).__init__()
        self.fname = fname
        self.inner = inner

    def __str__(self):
        """
        Provide a human-readable error message.
        """
        return 'Could not parse the {fname} netplan config file: {e}' \
               .format(fname=self.fname, e=self.inner)

    def __repr__(self):
        """
        Provide a Python-style representation.
        """
        return 'ParseFileException(fname={fname}, inner={inner})' \
               .format(fname=repr(self.fname), inner=repr(self.inner))


class Parser(object):
    """
    Provide functions for parsing the netplan configuration files.
    """

    # The default list of directories to look in.
    NETPLAN_DIRS = ('/lib/netplan', '/etc/netplan', '/run/netplan')

    # The section names for the various interface classes.
    BY_SECTION = {
        'bonds': npiface.BondInterface,
        'bridges': npiface.BridgeInterface,
        'ethernets': npiface.EthernetInterface,
        'vlans': npiface.VLANInterface,
        'wifis': npiface.WirelessInterface,
    }

    def __init__(self, dirs=NETPLAN_DIRS):
        """
        Initialize a Parser object, possibly overriding
        the list of directories to look in for netplan config files.
        """
        self.dirs = dirs

    def find_files(self):
        """
        Return a list of the full pathnames to the files that will be
        parsed for the netplan configuration.
        """
        # Go through the directories in order, find all files with
        # names that end in *.yaml, then let a file in a later
        # directory override one by the same name in an earlier one.
        #
        files = dict(itertools.chain(
            *map(lambda d: filter(lambda i: os.path.isfile(i[1]),
                                  map(lambda f: (f, os.path.join(d, f)),
                                      filter(lambda s: s.endswith('.yaml'),
                                             os.listdir(d)))),
                 filter(os.path.isdir, self.dirs))))

        # Now return the full paths sorted by their base name.
        return [files[name] for name in sorted(files.keys())]

    def _combine_dicts(self, cur, new):
        """
        Combine the "cur" and "new" dictionaries:
        - if an item is only in "new", add it to "cur"
        - if an item is in both "cur" and "new", examine the item type:
          - if a list, append the new elements to it
          - if a dictionary, recursively combine the two
          - otherwise, override the "cur" item with the "new" one
        """
        for (key, value) in new.items():
            if key not in cur:
                cur[key] = value
            elif isinstance(value, list):
                cur[key].extend(value)
            elif isinstance(value, dict):
                self._combine_dicts(cur[key], value)
            else:
                cur[key] = value

    def _combine_files(self, files):
        """
        Read the netplan definitions from the specified files and, for
        each interface in them, create an object of the NetPlan*Interface
        type corresponding to the netplan section that the interface was
        defined in.
        """
        def parse_file(fname):
            """
            Parse a version 2 netplan file and return a dictionary
            containing the data about the interfaces.
            """
            with open(fname, mode='r') as infile:
                contents = yaml.load(infile)
            if not isinstance(contents, dict):
                raise Exception('The contents is not a YAML dictionary')
            net = contents.get('network')
            if net is None:
                raise Exception('No "network" top-level element')
            ver = net.get('version')
            if ver is None:
                raise Exception('No "network/version" element')
            elif ver != 2:
                raise Exception('Unsupported format version {ver}'
                                .format(ver=ver))
            del net['version']
            missing = sorted(set(net.keys()) - skeys)
            if missing:
                raise Exception('Unsupported section(s) {ms}'
                                .format(ms=', '.join(missing)))
            return net

        raw = {}
        skeys = set(self.BY_SECTION.keys())
        for fname in files:
            try:
                self._combine_dicts(raw, parse_file(fname))
            except Exception as exc:
                raise ParseFileException(fname=fname, inner=exc)

        data = {}
        for section, ifaces in raw.items():
            cls = self.BY_SECTION[section]
            for iface, idef in ifaces.items():
                data[iface] = cls(iface, section, idef)
        return data

    def parse(self, exclude=None):
        """
        Parse the netplan configuration files in the specified
        directories, possibly excluding certain files by name, and
        return a NetPlan object containing the parsed definitions.
        The "exclude" parameter is a list of the filenames (not full
        paths) of the files to be excluded, e.g. ["99-storpool.yaml"].
        """
        files = self.find_files()
        if exclude is not None:
            exs = set(exclude)
            files = [f for f in files if os.path.basename(f) not in exs]
        return npconfig.NetPlan(self._combine_files(files))
