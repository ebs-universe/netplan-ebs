#!/usr/bin/env python
#
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
A command-line tool for parsing the netplan configuration and outputting
various aspects in human- and machine-readable format.
"""

from __future__ import print_function


import argparse
import json
import yaml

import netplan


VERSION_STRING = '0.1.0.dev1'


def version():
    """Display program version information."""
    print('netplan-parser ' + VERSION_STRING)


def features():
    """Display program features information."""
    print('Features: netplan-parser=' + VERSION_STRING)


def parse_args(args):
    """
    Parse the netplan data and return either the full configuration or
    only the interfaces specified on the command line.
    """
    try:
        parser = netplan.Parser()
        data = parser.parse()
    except Exception as exc:
        exit('Could not parse the netplan data: {e}'.format(e=exc))

    if args.interfaces:
        missing = sorted(set(args.interfaces) - set(data.data.keys()))
        if missing:
            exit('No netplan data for {m}'.format(m=', '.join(missing)))
        ifaces = sorted(args.interfaces)
    else:
        ifaces = sorted(data.data.keys())

    return data, ifaces


FORMATTERS = {
    'brief': str,

    'json': lambda data: json.dumps({
        k: v.data for (k, v) in data.data.items()
    }),

    'names': lambda data: ' '.join(sorted(data.data.keys())),

    'yaml': lambda data: yaml.dump({
        k: v.data for (k, v) in data.data.items()
    }),
}


def output(data, args, default_format='yaml'):
    """
    Output the gathered data in the appropriate format: either explicitly
    requested by the user or the default for the query that produced it.
    """
    fmt = args.format if args.format else default_format
    global FORMATTERS
    print(FORMATTERS[fmt](data))


def cmd_show(args):
    """
    Show the full configuration of the specified interfaces.
    """
    data, ifaces = parse_args(args)
    selected = netplan.NetPlan({
        iface: data.data[iface] for iface in ifaces
    })
    output(selected, args)


def cmd_related(args):
    """
    Show the configuration of the specified interfaces and all other
    interfaces related to them, e.g. raw devices for VLANs, members for
    bridge and bond interfaces, etc.
    """
    data, ifaces = parse_args(args)
    selected = data.get_all_interfaces(ifaces)
    output(selected, args, default_format='names')


def cmd_physical(args):
    """
    Gather the configuartion of the specified interfaces and all other
    interfaces related to them, e.g. raw devices for VLANs, members for
    bridge and bond interfaces, etc; then show the configuration for
    the physical interfaces only.
    """
    data, ifaces = parse_args(args)
    selected = data.get_physical_interfaces(ifaces)
    output(selected, args, default_format='names')


def main():
    """
    Parse command-line options, run the query, output the results.
    """
    global FORMATTERS
    parser = argparse.ArgumentParser(
        prog='netplan-parser',
        usage='''
        netplan-parser [-f fmt] show [interface...]
        netplan-parser [-f fmt] physical interface...
        netplan-parser [-f fmt] related interface...
        netplan-parser -V | -h | --help | --version
        netplan-parser --features''')
    parser.add_argument('-N', '--noop', action='store_true',
                        help='no-operation mode')
    parser.add_argument('-V', '--version', action='store_true',
                        help='display program version information and exit')
    parser.add_argument('--features', action='store_true',
                        help='display program feature information')
    parser.add_argument('--format', '-f',
                        choices=sorted(FORMATTERS.keys()),
                        help='specify the output format')
    sub = parser.add_subparsers()

    parser_show = sub.add_parser('show')
    parser_show.add_argument('interfaces', type=str, nargs='*',
                             help='only examine the specified interfaces')
    parser_show.set_defaults(func=cmd_show)

    parser_physical = sub.add_parser('physical')
    parser_physical.add_argument('interfaces', type=str, nargs='+',
                                 help='the interfaces to examine')
    parser_physical.set_defaults(func=cmd_physical)

    parser_related = sub.add_parser('related')
    parser_related.add_argument('interfaces', type=str, nargs='+',
                                help='the interfaces to examine')
    parser_related.set_defaults(func=cmd_related)

    args = parser.parse_args()
    if args.version:
        version()
        exit(0)

    if args.features:
        features()
        exit(0)

    args.func(args)


main()
