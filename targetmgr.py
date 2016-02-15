#!/usr/bin/env python
"""
Wrapper for rtslib by ISG D-PHYS ETHZ to manage iSCSI targets.

Reads the configuration from `./targetmgr.json` and
creates the corresonding iSCSI targets.

Further documentation:
    - rtslib:  http://linux-iscsi.org/Doc/rtslib/html/

CLI options:
    --delete    deletes all existing iSCSI resources
    -h          show this help
    -d          show DEBUG output
"""

import getopt
import json
import logging
import os
import rtslib
import sys

# create logger
FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger('targetmaker')


# --- Config Helper Functions ---
def target_index_by_iqn(iqn):
    """
    Given the iqn of a target, returns the target's index in the iscsi_config['targets'] list.
    Returns None if no matching iqn could be found.
    """
    for (index, target) in enumerate(iscsi_config['targets']):
        if target['iqn'] == iqn:
            return index

    return None


# --- Backstore and iblock Functions ---
def _next_free_backstore_index():
    """
    Returns a non-allocated backstore index.
    """
    backstore_indices = [backstore.index for backstore in rtslib.root.RTSRoot().backstores]
    if not backstore_indices:
        next_free_index = 0
    else:
        next_free_index = max(backstore_indices) + 1

    return next_free_index


def current_iblocks():
    """
    Returns list of currently defined iblocks,
    each being represented as {'device': '<udev-path>', 'name': '<str>'}.
    """
    existing_iblocks = []
    for backstore in rtslib.root.RTSRoot().backstores:
        for storage_object in backstore.storage_objects:
            existing_iblocks.append(
                {
                    'name':   storage_object.name,
                    'device': storage_object.udev_path,
                    'index':  storage_object.backstore.index,
                }
            )

    return existing_iblocks


def create_iblock(iblock):
    """
    Given an iblock {'device': '<udev-path>', 'name': '<str>'},
    checks if it already exists in the backstore or creates it.
    """
    logger.info("trying to create backstore %s" % iblock['name'])
    if iblock['name'] in (lun['name'] for lun in current_iblocks()):
        logger.debug("iblock %s already exists" % iblock['name'])
    elif iblock['device'] in (lun['device'] for lun in current_iblocks()):
        logger.debug("iblock device %s already in use" % iblock['device'])
    else:
        logger.debug("Creating iblock %s" % iblock['name'])
        backstore = rtslib.IBlockBackstore(_next_free_backstore_index(), mode='create')
        try:
            rtslib.IBlockStorageObject(backstore, iblock['name'], iblock['device'], gen_wwn=True)
        except:
            backstore.delete()
            raise

    return None


def delete_all_backstores():
    """
    Recursively deletes all Backstore objects.
    """
    for backstore in rtslib.root.RTSRoot().backstores:
        backstore.delete()

    return None


# --- iSCSI Target Functions ---
def current_targets():
    """
    Returns list of iqn's of currently defined iscsi targets.
    """
    existing_targets = []
    for target in rtslib.FabricModule('iscsi').targets:
        existing_targets.append(
            target.wwn,
        )

    return existing_targets


def create_target(iqn):
    """
    Creates new iscsi target with given iqn, unless it already exists.
    """
    logger.info("trying to create target %s" % iqn)
    if iqn in current_targets():
        logger.debug('iscsi-target "%s" already exists' % iqn)
    else:
        try:
            rtslib.Target(rtslib.FabricModule('iscsi'), wwn=iqn)
            logger.debug('Creating iscsi-target %s' % iqn)
        except:
            raise

    return None


def delete_all_targets():
    """
    Recursively deletes all iscsi Target objects.
    """
    for iqn in current_targets():
        rtslib.Target(rtslib.FabricModule('iscsi'), wwn=iqn).delete()

    return None


def delete_fabric():
    """
    Delete iscsi fabric object.
    """
    # delete folder /sys/kernel/config/target/iscsi
    rtslib.node.CFSNode.delete(rtslib.FabricModule('iscsi'))


# --- TPG Functions ---
def _get_single_tpg(iqn):
    """
    Returns TPG object for given iqn, assuming that each target has a single TPG.
    """
    tpg = rtslib.TPG(rtslib.Target(rtslib.FabricModule('iscsi'), iqn), 1)

    return tpg


def current_tpgs(iqn):
    """
    Returns list of currently defined TPGs on iscsi target with given iqn,
    each being represented as {'iqn': '<str>', 'tag': '<int>'}
    """
    existings_tpgs = []
    for tpg in rtslib.Target(rtslib.FabricModule('iscsi'), iqn).tpgs:
        existings_tpgs.append(
            {
                'iqn': iqn,
                'tag': tpg.tag,
            }
        )

    return existings_tpgs


def _next_free_tpg_index(iqn):
    """
    Returns a non-allocated TPG index on iscsi target with given iqn.
    """
    tpg_indices = [tpgs['tag'] for tpgs in current_tpgs(iqn)]
    if not tpg_indices:
        next_free_index = 1
    else:
        next_free_index = max(tpg_indices) + 1

    return next_free_index


def create_tpg(iqn):
    """
    Creates new TPG on iscsi target with given iqn.
    """
    logger.info("trying to create new tpg for %s" % iqn)
    try:
        rtslib.TPG(rtslib.Target(rtslib.FabricModule('iscsi'), iqn), _next_free_tpg_index(iqn))
    except:
        raise

    return None


def set_custom_tpg_attributes(iqn):
    tpg_attributes = dict(
        authentication='0',
        cache_dynamic_acls='1',
        demo_mode_write_protect='0',
        generate_node_acls='1',
    )
    for attribute, value in tpg_attributes.items():
        if _get_single_tpg(iqn).get_attribute(attribute) != value:
            _get_single_tpg(iqn).set_attribute(attribute, value)
            logger.debug('tpg attribute %s has been set to value %s' % (attribute, value))

    return None


def enable_tpg(iqn, status):
    """
    Enables or disables the TPG. Raises an error if trying to disable a TPG without en enable attribute (but enabling works in that case).
    """
    _get_single_tpg(iqn)._set_enable(status)


# --- Portal Functions ---
def current_portals(iqn):
    """
    Returns list of current portals.
    """
    existing_portals = []
    for portal in _get_single_tpg(iqn).network_portals:
        existing_portals.append(
            {
                'ip':   portal.ip_address,
                'port': portal.port,
            }
        )

    return existing_portals


def create_portal(iqn, ip, port=3260):
    """
    Creates portal on TPG with given iqn to destination with given ip and port (default 3260).
    """
    logger.info("trying to create new portal for %s" % iqn)
    _get_single_tpg(iqn).network_portal(ip, port, mode='any')

    return None


# --- ACL Functions ---
def current_acls(iqn):
    """
    Returns list of iqn's of current ACLs in given target
    """
    existing_acls = []
    for node_acl in _get_single_tpg(iqn).node_acls:
        existing_acls.append(
            node_acl.node_wwn
        )

    return existing_acls


def create_acl(iqn, iqn_initiator):
    """
    Creates new acl with given iqn, unless it already exists.
    """
    logger.info("trying to create new acl for %s" % iqn)

    if iqn_initiator in current_acls(iqn):
        logger.debug('acl with iqn %s already exists' % iqn)
    else:
        try:
            _get_single_tpg(iqn).node_acl(iqn_initiator, mode='create')
        except:
            raise

    return None


# --- LUN Functions ---
def _get_lun_id(iqn, name):
    for curlun in current_attached_luns(iqn):
        if name == curlun['name']:
            return curlun['lun']


def _next_free_lun_index(iqn):
    """
    Returns a non-allocated lun index.
    """
    lun_indices = [lun.lun for lun in _get_single_tpg(iqn).luns]
    if not lun_indices:
        next_free_index = 0
    else:
        next_free_index = max(lun_indices) + 1

    return next_free_index


def _next_free_mapped_lun_index(iqn, iqn_initiator):
    """
    Returns a non-allocated mapped_lun index.
    """
    mapped_lun_indices = [
        mapped_lun['lun'] for mapped_lun in current_mapped_luns(iqn, iqn_initiator)
    ]
    if not mapped_lun_indices:
        next_free_index = 0
    else:
        next_free_index = max(mapped_lun_indices) + 1

    return next_free_index


def current_attached_luns(iqn):
    """
    Returns list of currently attached luns in given target (resp tpg),
    each being represented as {'lun': '<id>', 'name': '<str>', 'device': '<udev-path>'}.
    """
    attached_luns = []
    for lun in _get_single_tpg(iqn).luns:
        attached_luns.append(
            {
                'lun':    lun.lun,
                'name':   lun.storage_object.name,
                'device': lun.storage_object.udev_path,
            }
        )

    return attached_luns


def current_mapped_luns(iqn, iqn_initiator):
    """
    Returns list of currently mapped luns in given acl (resp tpg),
    each being represented as {'lun': '<id>'}.
    """
    mapped_luns = []
    for mapped_lun in rtslib.NodeACL(_get_single_tpg(iqn), iqn_initiator).mapped_luns:
        mapped_luns.append(
            {
                'lun': mapped_lun.mapped_lun,
            }
        )

    return mapped_luns


def create_attached_lun(iqn, iblock_name):
    """
    Creates new lun for given tpg.
    """
    logger.info("trying to attach %s to %s" % (iblock_name, iqn))
    if iblock_name in (curlun['name'] for curlun in current_attached_luns(iqn)):
        logger.debug("LUN %s already exists" % iblock_name)
    else:
        for iblock in current_iblocks():
            if iblock['name'] == iblock_name:
                rtslib.LUN(
                    _get_single_tpg(iqn),
                    _next_free_lun_index(iqn),
                    storage_object=rtslib.IBlockStorageObject(
                        rtslib.IBlockBackstore(iblock['index'], mode='lookup'), iblock['name']
                    )
                )

    return None


def create_mapped_lun(iqn, iqn_initiator, lun):
    """
    Map a lun to given acl.
    """
    logger.info("trying to map LUN %s for %s" % (lun, iqn))
    if lun in (curlun['name'] for curlun in current_attached_luns(iqn)):
        if {'lun': _get_lun_id(iqn, lun)} in current_mapped_luns(iqn, iqn_initiator):
            logger.debug("Mapped_LUN %s still exists" % lun)
        else:
            try:
                rtslib.MappedLUN(
                    _get_single_tpg(iqn).node_acl(iqn_initiator, mode='lookup'),
                    _next_free_mapped_lun_index(iqn, iqn_initiator),
                    tpg_lun=_get_lun_id(iqn, lun)
                )
            except:
                raise
    else:
        logger.debug("LUN %s does not exists" % lun)

    return None


def save_to_disk():
    os.system("echo -e 'ls\nsaveconfig\nyes' | targetcli >/dev/null")


def read_target_config():
    """
    Read the configfile.
    """
    with open(os.path.dirname(os.path.abspath(__file__)) + '/targetmgr.json', 'r') as json_file:
        config = json.load(json_file)

    return config


# --- Main Function ---
if __name__ == '__main__':

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd", ["help", "delete"])
    except getopt.GetoptError:
        print __doc__
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print __doc__
            sys.exit()
        elif opt == '-d':
            logger.setLevel(logging.DEBUG)
        elif opt == '--delete':
            logger.info("cleanup target resources!")
            delete_all_targets()
            delete_all_backstores()
            delete_fabric()
            logger.info("done!")
            sys.exit()

    if rtslib.root.RTSRoot().backstores:
        print("Backstores existing!")
        sys.exit()

    if rtslib.FabricModule('iscsi').targets:
        print("Existing targets!")
        sys.exit()

    logger.info("Check for LIO_CFS_DIR")
    LIO_CFS_DIR = "/sys/kernel/config/target/iscsi"
    if not os.path.exists(LIO_CFS_DIR):
            os.makedirs(LIO_CFS_DIR)

    logger.info("read configfile")
    iscsi_config = read_target_config()

    for target in iscsi_config['targets']:
        create_target(target['iqn'])

        # create portals --> creates tpgt1 also!
        create_portal(target['iqn'], target['portal'])

        create_acl(target['iqn'], target['iqn_initiator'])

        set_custom_tpg_attributes(target['iqn'])

        for lun in iscsi_config['targets'][target_index_by_iqn(target['iqn'])]['luns']:
            create_iblock(lun)
            create_attached_lun(target['iqn'], lun['name'])
            create_mapped_lun(
                target['iqn'],
                target['iqn_initiator'],
                lun['name']
            )

        enable_tpg(target['iqn'], 1)

    save_to_disk()
