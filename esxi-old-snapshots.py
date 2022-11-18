#!/usr/bin/env python3

"""
Author - Kostya Belykh k@belykh.su
Language - Python 3.8+
This script is designed to find on all vms in vcenter old snapshots with ability
to be filtered by name of snapshot
"""

from optparse import OptionParser
from datetime import datetime, tzinfo, timedelta
from urllib.parse import urlparse
import sys
import logging
import time
import ssl
import atexit
import threading
try:
    from pyVim.connect import SmartConnect, Disconnect
    from pyVmomi import vim # type: ignore
except ImportError:
    sys.exit('Failed to import pyvim module. Try "pip3 install pyvmomi"')

start       = time.time()
logger      = logging.getLogger()

# Defining properly UTC timezone as class for use in compare
# https://stackoverflow.com/a/2331635
ZERO = timedelta(0)
class UTC(tzinfo):
  def utcoffset(self, dt):
    return ZERO
  def tzname(self, dt):
    return "UTC"
  def dst(self, dt):
    return ZERO
utc = UTC()

def parseCommandOptions():

    # Parsing input parameters
    p = OptionParser(add_help_option=False,
                     usage = '%prog [options]'
    )
    p.add_option('--help',
                 action = 'store_true',
                 dest = 'help',
                 help = 'Show this message and exit'
    )
    p.add_option("--vcenter",
                 dest="vcenter",
                 help="Vcenter IP address. Mandatory option."
    )
    p.add_option("--username",
                 dest="username",
                 help="Vcenter username. Mandatory option."
    )
    p.add_option("--password",
                 dest="password",
                 help="Vcenter password. Mandatory option."
    )
    p.add_option("--name",
                 dest="name",
                 help="Exact VM snapshot name to search. If not passed - sear" +
                 "ching for all snapshots"
    )
    p.add_option("--time",
                 dest="timeold",
                 help="Number of seconds of snapshot oldiness. Can be used " + 
                      "with time suffixes such as 'd', 'h', 'm', 'w', eg: " +
                      "'48h' or '2d'. Mandatory option."
    )  
    p.add_option('-l', '--logging',
                 dest = 'enablelogging',
                 help = 'Enable logging to STDOUT',
                 action='store_true'
    )

    (options, args) = p.parse_args()

    if options.help:
        p.print_help()
        exit()

    ## Setup logging
    if options.enablelogging:
        loglevel = 'INFO'
        logFormatStr = '%(asctime)s - %(levelname)-8s - %(message)s'
        logger.setLevel(loglevel)
        chandler = logging.StreamHandler()
        formatter = logging.Formatter(logFormatStr)
        chandler.setFormatter(formatter)
        logger.addHandler(chandler)
    if not options.name:
        # Assuming we don't have name, so we checking only age of snapshot
        options.name = str()

    if (
        options.vcenter
        and options.username
        and options.password
        and options.timeold
    ):
        main(
            options.vcenter,
            options.username,
            options.password,
            options.name,
            options.timeold
        )
    else:
        sys.exit("The required parameters is missing. Runtime parameters: " +\
                  str(sys.argv[1:]))

def timetoseconds(strtime):
    """Function to convert string with time suffix to int of seconds"""
    # Minute to seconds
    # 1m = 60
    if 'm' in strtime:
        strtime = strtime.replace('m','')
        return (int(strtime) * 60)
    # Hour to seconds
    # 1h = 60 * 60
    if 'h' in strtime:
        strtime = strtime.replace('h','')
        return (int(strtime) * 60 * 60)
    # Day to seconds
    # 1d = 60 * 60 * 24
    if 'd' in strtime:
        strtime = strtime.replace('d','')
        return (int(strtime) * 60 * 60 * 24)
    # Week to seconds
    # 1w = 60 * 60 * 24 * 7
    if 'w' in strtime:
        strtime = strtime.replace('w','')
        return (int(strtime) * 60 * 60 * 24 * 7)
    # Seconds to seconds
    # I know it's kinda sounds stupid but i need
    #  to strip letter s from str and make it int
    if 's' in strtime:
        strtime = strtime.replace('s','')
        return (int(strtime))
    # If no letters passed just return as int
    return (int(strtime))

def patch_ssl():
    """Support self-signed vCenter certificates."""
    import requests
    import requests.packages.urllib3.exceptions as rexc # type: ignore
    for warning in [rexc.InsecureRequestWarning, rexc.InsecurePlatformWarning]:
        requests.packages.urllib3.disable_warnings(warning)
        # logging.getLogger('urllib3').setLevel(logging.WARNING)
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
        pass
    except Exception:
        pass

def vmWorker(vm, name, timeold):
    """Worker to find VMs with old snapshots"""
    if vm.snapshot:
        try:
            for snapshot in vm.snapshot.rootSnapshotList:
                if name in snapshot.name:
                    # Calculating time delta from creating snapshot to now
                    delta = datetime.now(utc) - snapshot.createTime
                    if int(delta.total_seconds()) > timetoseconds(timeold):
                        print('VM {} has snapshot "{}" older than {}'.format(
                            vm.summary.config.name,
                            snapshot.name,
                            timeold)
                        )
        except AttributeError:
            # Sometimes VM do not have attribute of Snapshot and can throw
            # attribute error 
            pass

def main(vcsa,
         username,
         password,
         name,
         timeold):
    logging.info('************************************************************')
    logging.info('Script started')

    logging.info('Patching SSL for use self-signed certificates')
    patch_ssl()
    logging.info('Connecting to VCenter {}'.format(vcsa))

    if '//' in vcsa:
        #stripping VCSA from url to ip\fqdn
        vcenter = urlparse(vcsa).netloc
    else:
        vcenter = vcsa
    if not vcenter:
        logging.error('Can\'t parse URL from supplied VCenter address')
        sys.exit('Can\'t parse URL from supplied VCenter address')

    try:
        si = SmartConnect(host=vcenter,
                          user=username,
                          pwd=password,
                          port=443,
                          sslContext=None,
                          connectionPoolTimeout=2)
    except Exception as e:
        logging.error('Error connecting: {}'.format(e))
        sys.exit('Error connecting: {}'.format(e))

    atexit.register(Disconnect, si)

    logging.info('Gathering list of all VMs')
    content = si.RetrieveContent()  #Creating instance 
    container = content.rootFolder  #Setiing to look from root folder
    viewType = [vim.VirtualMachine] #Type of object to look for
    recursive = True
    containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive)
    children = containerView.view
    logging.info('Checking vm for snapshots with name {} older than {}'.format(
        name, 
        timeold)
    )
    logging.info('Number of VMs found - {}'.format(len(children)))

    workers = list()
    for vm in children:
        worker = threading.Thread(target=vmWorker,
                                  args=(vm,name,timeold))
        workers.append(worker)
    for w in workers:
        w.start()
    for w in workers:
        w.join()

    logging.info('Script finished. Runtime: {} seconds.'.format(
        str(round(time.time() - start, 3))
        )
    )

if __name__ == '__main__':
    parseCommandOptions()