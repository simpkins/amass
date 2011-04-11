#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
"""
CD-ROM implementation using the Linux sg driver.
"""

import array
import ctypes
import fcntl
import os
import struct
import time

from ... import cbuf
from ... import scsi_sg as sg
from .. import _err

# Defined by the Mt. Fuji specification,
# and the SCSI MMC specifications.
CMD_READ_TOC_PMA_ATIP = 0x43

# Linux CD constants, defined in linux/cdrom.h
CDROMEJECT = 0x5309
CDROMCLOSETRAY = 0x5319
CDROM_DRIVE_STATUS = 0x5326

CDS_NO_INFO = 0
CDS_NO_DISC = 1
CDS_TRAY_OPEN = 2
CDS_DRIVE_NOT_READY = 3
CDS_DISC_OK = 4

DEFAULT_READY_TIMEOUT = 15


class Device(object):
    def __init__(self, name, timeout=DEFAULT_READY_TIMEOUT, wait_ready=True):
        self.name = name
        self.fd = -1 # so self.fd exists in __del__ if open() fails

        # Open with O_NONBLOCK.  Otherwise the open will fail if the drive
        # is not ready or doesn't have a disc.  Using O_NONBLOCK allows us to
        # open it anyway, so we can use wait_until_ready() to close the drive
        # and wait until it does become ready.  (At least on the drive I have,
        # a normal open without O_NONBLOCK will close the drive if it is open,
        # but then immediately fail because the drive reports
        # CDS_DRIVE_NOT_READY for a few seconds after closing.)
        self.fd = os.open(name, os.O_RDONLY | os.O_EXCL | os.O_NONBLOCK)
        if wait_ready:
            self.wait_until_ready(timeout)

    def __del__(self):
        if self.fd >= 0:
            self.close()

    def __str__(self):
        return self.name

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, ex_trace):
        self.close()

    def close(self):
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def get_drive_status(self):
        """
        get_drive_status() --> status

        Returns one of the CDS_* codes to indicate drive status.
        """
        slot_number = array.array('i', [0])
        return fcntl.ioctl(self.fd, CDROM_DRIVE_STATUS, slot_number)

    def wait_until_ready(self, timeout=DEFAULT_READY_TIMEOUT, close_tray=True):
        ret = self.get_drive_status()
        if ret == CDS_NO_INFO:
            # If the drive doesn't support querying the status,
            # just return immediately, and hope for the best.
            return

        if timeout < 0:
            end_time = -1
        else:
            end_time = time.time() + timeout

        # If the tray is open, close it
        if ret == CDS_TRAY_OPEN:
            if not close_tray:
                raise _err.TrayOpenError(self)
            self.close_tray()
            ret = self.get_drive_status()

        # Wait until the drive moves out of the NOT_READY state
        while ret == CDS_DRIVE_NOT_READY:
            # Don't wait longer than timeout seconds
            if end_time >= 0 and time.time() > end_time:
                break

            time.sleep(0.1)
            ret = self.get_drive_status()

        if ret == CDS_DISC_OK:
            return
        if ret == CDS_NO_DISC:
            raise _err.NoDiscError(self)
        raise _err.DriveNotReadyError(self)

    def eject(self):
        return fcntl.ioctl(self.fd, CDROMEJECT)

    def close_tray(self):
        return fcntl.ioctl(self.fd, CDROMCLOSETRAY)


def ReadTocPmaAtipCmd(format, number, output_length, want_msf=False):
    cmd = cbuf.CBuffer(12)
    cmd[0] = CMD_READ_TOC_PMA_ATIP
    if want_msf:
        cmd[1] = 0x2
    cmd[2] = format
    cmd[6] = number
    if output_length < 0:
        raise ValueError('output_length (%s) may not be negative' %
                         (output_length,))
    if output_length > 0xffff:
        raise ValueError('output_length (%s) must be less than %d' %
                         (output_length, 0x10000))
    cmd[7] = (output_length >> 8) & 0xff
    cmd[8] = (output_length & 0xff)
    return cmd.buf


def read_toc(device, format, number, want_msf=False, output_len_hint=1024):
    if isinstance(device, (str, unicode)):
        device = Device(device)

    output_len = output_len_hint
    for n in range(2):
        output = cbuf.CBuffer(output_len)
        cmd = ReadTocPmaAtipCmd(format=format, number=number,
                                output_length=len(output), want_msf=want_msf)
        sg.sg_cmd(device.fd, sg.SG_DXFER_FROM_DEV, cmd=cmd, dxfer=output.buf)

        data_len = output.getU16BE(0)
        if data_len + 2 > len(output):
            # Re-run the command with a larger output length
            output_len = data_len + 2
            continue

        return output[0:data_len + 2]

    # If we reach here, the data length was too small even on the second
    # time around the loop.  This shouldn't happen.
    raise Exception('failed to read full TOC: adjusted data length (%d) '
                    'was still too small' % (output_len,))

def read_simple_toc(device, want_msf=False):
    return read_toc(device, format=0, number=0, want_msf=want_msf)


def read_session_info(device, want_msf=False):
    return read_toc(device, format=1, number=0, want_msf=want_msf)


def read_full_toc(device):
    return read_toc(device, format=2, number=0)


def read_cd_text(device):
    try:
        return read_toc(device, format=5, number=0)
    except sg.StdCheckConditionError, ex:
        # We only handle certain SENSE_ILLEGAL_REQUEST errors.
        # re-raise all other errors
        if ex.senseKey != sg.SENSE_ILLEGAL_REQUEST:
            raise

        if ex.additionalSenseCode == sg.SENSE_ADDL_ILLEGAL_MODE_FOR_TRACK:
            # Code 0x64 (Illegal mode for this track) means
            # the CD does not contain CD-TEXT info.
            raise _err.NoCdTextError(device)
        elif ex.additionalSenseCode == sg.SENSE_ADDL_ILLEGAL_CDB_FIELD:
            # Code 0x24 (Illegal field in cdb) means the CD-ROM device
            # did not understand the request.  This is probably an older
            # drive that does not support CD-TEXT.
            raise _err.CdTextNotSupportedError(device)

        # Unknown error.  re-raise it as-is
        raise
