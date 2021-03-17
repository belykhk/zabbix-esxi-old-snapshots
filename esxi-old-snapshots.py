#! /bin/python3

# Author
## k@belykh.su
# Description
## This script is designed to find on all vms in vcenter old snapshots
## filtered by name of snapshot

from optparse import OptionParser
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from datetime import datetime, tzinfo, timedelta
import logging
import time
import ssl
import requests
import atexit

start  = time.time()
logger = logging.getLogger()

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

    p = OptionParser(add_help_option=False,
                     usage="%prog [options]")
    p.add_option("--help",
                 action="store_true",
                 dest="help",
                 help="Show this message and exit.")
    p.add_option("-v", "--vcenter",
                 dest="vcenter",
                 help="Vcenter IP address. Mandatory option.")
    p.add_option("-u", "--username",
                 dest="username",
                 help="Vcenter username. Mandatory option.")
    p.add_option("-p", "--password",
                 dest="password",
                 help="Vcenter password. Mandatory option.")
    p.add_option("-n", "--name",
                 dest="name",
                 help="Exact VM snapshot name to search. Mandatory option.")
    p.add_option("-t", "--time",
                 dest="timeold",
                 help="Number of seconds of snapshot oldiness. Can be used " + 
                      "with time suffixes such as 'd', 'h', 'm', eg: '48h' or "+
                      "'2d'. Mandatory option.")          
    p.add_option("-l", "--logging",
                 dest="logging",
                 help="Logging level. If not passed - didn't log.")

    (options, args) = p.parse_args()

    if options.help:
        p.print_help()
        exit()

    # Setup logging
    if options.logging:
        loglevel       = str(options.logging)
        logFormatStr   = '%(asctime)s - %(levelname)-8s - %(message)s'
        handler = logging.StreamHandler()
        formatter = logging.Formatter(logFormatStr)
        logger.setLevel(loglevel)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if not options.vcenter or not \
        options.username or not \
        options.password or not \
        options.name or not \
        options.timeold:
        print('Not all mandatory options passed. Check with --help')
        exit()
    else:
        main(options.vcenter,
             options.username,
             options.password,
             options.name,
             options.timeold)

def patch_ssl():
    """Support self-signed vCenter certificates."""
    import requests
    import requests.packages.urllib3.exceptions as rexc
    for warning in [rexc.InsecureRequestWarning, rexc.InsecurePlatformWarning]:
        requests.packages.urllib3.disable_warnings(warning)
        # logging.getLogger('urllib3').setLevel(logging.WARNING)
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
        pass
    except Exception:
        pass
 
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


def main(vcenter, username, password, name, timeold):
    logging.info('************************************************************')
    logging.info('Script started')

    logging.info('Patching SSL for use self-signed certificates')
    patch_ssl()
    logging.info('Connecting to VCenter {}'.format(vcenter))

    context = None
    si = SmartConnect(host=vcenter,
                      user=username,
                      pwd=password,
                      port=443,
                      sslContext=context)

    if not si:
        logging.error('Could not connect to VCenter {}'.format(vcenter))
        exit()
    
    atexit.register(Disconnect, si)

    logging.info('Gathering list of all VMs')
    content = si.RetrieveContent()  #Creating instance 
    container = content.rootFolder  #Setiing to look from root folder
    viewType = [vim.VirtualMachine] #Type of object to look for
    recursive = True
    containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive)
    children = containerView.view
    logging.info('Checking vm for snapshots with name {} older than {}'.format(name, 
                                                                                timeold))
    logging.info('Number of VMs found - {}'.format(len(children)))
    for vm in children:
        if vm.snapshot:
            for snapshot in vm.snapshot.rootSnapshotList:
                if name in snapshot.name:
                    # Calculating time delta from creating snapshot to now
                    delta = datetime.now(utc) - snapshot.createTime
                    if int(delta.total_seconds()) > timetoseconds(timeold):
                        print('VM {} has snapshot {} older than {}'.format(vm.summary.config.name,
                                                                           snapshot.name,
                                                                           timeold))

    logging.info('Script finished. Runtime: ' + \
                str(round(time.time() - start, 3)) + ' seconds.')

if __name__ == "__main__":
    parseCommandOptions()
