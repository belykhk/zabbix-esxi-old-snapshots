# Zabbix-ESXi-old-snapshots

Tool to search old snaphots in VCenter with specified name and Zabbix template to use with.

This script is designed for searching stuck Veeam snapshots of Virtual Machines, but can be used to search any snapshots with certain name and age.

## Prerequiements

1) Installed and working python3 with standart library
2) Installed VMware Python API SDK:
```
pip3 install setuptools --upgrade
pip3 install pyvmomi
```

## Usage of script (copypaste from '--help'):

    Usage: esxi-old-snapshots.py [options]
    
    Options:
      --help                Show this message and exit.
      -v VCENTER, --vcenter=VCENTER
                            Vcenter IP address. Mandatory option.
      -u USERNAME, --username=USERNAME
                            Vcenter username. Mandatory option.
      -p PASSWORD, --password=PASSWORD
                            Vcenter password. Mandatory option.
      -n NAME, --name=NAME  Exact VM snapshot name to search. Mandatory option.
      -t TIMEOLD, --time=TIMEOLD
                            Number of seconds of snapshot oldiness. Can be used
                            with time suffixes such as 'd', 'h', 'm', eg: '48h' or
                            '2d'. Mandatory option.
      -l LOGGING, --logging=LOGGING
                            Logging level. If not passed - didn't log.
                            

## Use with zabbix

1) Clone repository
2) Import .xml file into Zabbix as Template
3) Deploy .py script on to Zabbix server to externalscripts folder
4) Edit script attributes, eg:
```
chmod +x esxi-old-snapshots.py
chown zabbix:zabbix esxi-old-snapshots.py
```
5) Check that VMware Python API SDK installed on server (see Prerequiements)
6) Apply template `Template Module VMware old snapshots` to host