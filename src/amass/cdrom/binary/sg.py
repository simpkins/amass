#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
"""
CD-ROM implementation using the Linux sg driver.
"""

import ctypes
import fcntl
import os
import struct

from ... import cbuf
from ... import scsi_sg as sg

# Defined by the Mt. Fuji specification,
# and the SCSI MMC specifications.
CMD_READ_TOC_PMA_ATIP = 0x43


class Device(object):
    def __init__(self, name):
        self.fd = os.open(name, os.O_RDONLY | os.O_EXCL)

    def __del__(self):
        if self.fd >= 0:
            self.close()

    def close(self):
        os.close(self.fd)
        self.fd = -1


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
    # FIXME: If the CD doesn't contain CD-TEXT info,
    # a CheckConditionError is raised, with a sense code of
    # SENSE_ILLEGAL_REQUEST (0x5) and an additional sense code of 0x64
    # (Illegal mode for this track).
    #
    # When READ TOC/PMA/ATIP is called with an illegal format, a
    # CheckConditionError is raised with a sense code of SENSE_ILLEGAL_REQUEST
    # and an additional sense code of 0x24 (Invalid field in cdb)
    #
    # We can probably use this to distinguish between no CD-TEXT info,
    # and drives that don't support CD-TEXT.
    return read_toc(device, format=5, number=0)
