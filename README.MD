# Zabbix-ESXi-old-snapshots

Tool to search old snaphots in VCenter with specified name and Zabbix template to use with.

This script is designed for searching stuck Veeam snapshots of Virtual Machines, but can be used to search any snapshots with certain name and (or) age.

## Prerequiements

1) Installed and working python3 with standart library
2) Installed VMware Python API SDK:
```
python3 -m pip install setuptools --upgrade
python3 -m pip install pyvmomi
```

## Usage of script (copypaste from '--help'):

    Usage: esxi-old-snapshots.py [options]
    
    Options:
      --help               Show this message and exit
      --vcenter=VCENTER    Vcenter IP address. Mandatory option.
      --username=USERNAME  Vcenter username. Mandatory option.
      --password=PASSWORD  Vcenter password. Mandatory option.
      --name=NAME          Exact VM snapshot name to search. If not passed -
                           searching for all snapshots
      --time=TIMEOLD       Number of seconds of snapshot oldiness. Can be used
                           with time suffixes such as 'd', 'h', 'm', 'w', eg:
                           '48h' or '2d'. Mandatory option.
      -l, --logging        Enable logging to STDOUT
                            

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
6) Apply template `Template module VMware VCSA old snapshots` to host