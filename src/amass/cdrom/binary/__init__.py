#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#

"""
This file aims to provide a low-level python interface to CD-ROM devices.

This module itself is just a wrapper to import the correct implementation for
this platform.
"""

def _get_sg_driver_version():
    """
    Get the version of the linux sg driver.

    Returns the version number as an integer.
    Returns None on non-linux systems, or if the sg driver or not present.
    None is also returned for older sg versions that do not report a version
    number (before version 20000).
    """
    SCSI_VERSION_FILE = '/proc/scsi/sg/version'
    f = None
    try:
        f = open(SCSI_VERSION_FILE, 'r')
        data = f.readline()
        return int(data.split()[0])
    except:
        if f is not None:
            f.close()
        return None

def _has_usable_sg_driver():
    sg_version = _get_sg_driver_version()
    if sg_version is None:
        return False
    return sg_version >= 30000

if _has_usable_sg_driver():
    # Use the sg driver
    from . import sg as impl
else:
    # TODO: we could add other implementations in the future
    msg = 'no supported CD-ROM implementation for this platform'
    raise NotImplementedError(msg)


# Import impl methods into our namespace
Device = impl.Device
read_simple_toc = impl.read_simple_toc
read_session_info = impl.read_session_info
read_full_toc = impl.read_full_toc
read_cd_text = impl.read_cd_text


#
# Some generic utility functions
#

def parse_adr_ctrl(adr_ctrl):
    """
    Split a combined adr/ctrl byte into separate adr and ctrl fields
    """
    adr = (adr_ctrl >> 4) & 0xf
    ctrl = adr_ctrl & 0xf
    return (adr, ctrl)


def combine_adr_ctrl(adr, ctrl):
    """
    Combine the adr and ctrl fields into a single adr_ctrl byte.
    """
    assert adr <= 0xf
    assert ctrl <= 0xf
    return (adr << 4) | ctrl
