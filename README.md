# netplan - a Python library for parsing the netplan configuration data.

## About this Fork

This fork simply packages existing work done by other people, including :
  - The original `netplan` Python library, written by Peter Pentchev as part of 
    the [OpenStack development][openstack-dev] team at [StorPool][storpool].
  - Changes made by @jjacque of [Algolia][algolia] in [their fork][algolia/python-netplan].

Unfortunately, version presently on PyPI breaks on Ubuntu 20.04 and is
unusable. Additionally : 

  - The original author seems uninterested in continuing development and 
    changes have not been published for 3 years. 
  - The Algolia fork seems to have created debian packages, but I can't
    find them anywhere. It has seen recent development, though, 
    so I hope at some point the packages will become available.

This is forked from `algolia/python-netplan` for the sole purpose of making 
it pip installable. This fork will be made available as the `netplan-ebs` 
package on PyPI. 

Though the package will be installed as `netplan-ebs`, the actual 
importable package will still be `netplan`. Due to this, this fork 
and upstream cannot coexist in the same python environment. 

This package contains no EBS-specific code and adds no additional 
dependencies from upstream. 

If you are considering using this: 

  - I do not really have the bandwidth to maintain this fork. I will 
  make the best effort to keep this package installable and track any 
  changes from upstream, but that's about it.
  - If upstream resumes development, or publishes an installable package 
  either through `pip` or `apt` though a PPA, this fork and the associated 
  pypi package will likely become unmaintained.
  - Issues dealing with install and basic functionality are welcome. 
  - Pull Requests should ideally be sent to `algolia/python-netplan`, 
  so that the codebase does not diverge for entirely non-technical reasons.
  - If you are able and willing to take over maintenance of this package, 
  please get in touch with me. 

If you do end up using this package - especially if you do so in a 
production setting - please reach out to me and let me know by email at 
shashank at chintal dot in. The number of users, if any, is likely to 
determine how much effort I will put into maintaining this.

## Description

This module parses the YAML configuration files describing the system's
network configuration in the format used by the netplan.io package.
The main parser is the "netplan.parser.Parser" class (also exported as
"netplan.Parser"); its "parse()" method returns a data structure of
the "netplan.config.NetPlan" class (also exported as "netplan.NetPlan").

## Example usage

    import netplan

    p = netplan.Parser()
    data = p.parse()
    for iface, cfg in data.items():
        print('{section}/{name}'.format(section=cfg.section, name=iface)

    p = netplan.Parser()
    data = p.parse(exclude=['set-mtu.yaml'])
    fix = {'version': 2}
    for iface, cfg in data.get_all_interfaces(['br-enp4s0']).data.items():
        if cfg.get('mtu') != 9000:
            if cfg.section not in fix:
                fix[cfg.section] = {}
            fix[cfg.section][iface] = {'mtu': 9000}
    fix = {'network': fix}
    with open('/etc/netplan/set-mtu.yaml', mode='w') as f:
        print(yaml.dump(fix), file=f, end='')

## The netplan-parser tool

The three types of queries - parse the interface data, get all related
interfaces, and get only the physical related interfaces - are also
available via the command-line `netplan-parser` tool:

    # Show the configuration of all interfaces in YAML format
    netplan-parser show

    # Show the configuration of the specified interfaces in JSON format
    netplan-parser -f json show eno1 eno2.617

    # List the names of the interfaces related to the specified one
    netplan-parser -f names related eno2.617

    # Show the configuration of the physical interfaces related to
    # the specified ones
    netplan-parser --format=json physical eno2.617 br1-eno1

## Contact

The `netplan` Python library was written by Peter Pentchev as part of
the [OpenStack development][openstack-dev] team at [StorPool][storpool].

[openstack-dev]: mailto:openstack-dev@storpool.com
[storpool]: https://storpool.com/
[algolia]: https://www.algolia.com/
[algolia/python-netplan]: https://github.com/algolia/python-netplan
