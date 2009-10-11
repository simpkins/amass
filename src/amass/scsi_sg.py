#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import ctypes

from . import cbuf

# Constants from scsi/sg.h
SG_DXFER_NONE = -1
SG_DXFER_TO_DEV = -2
SG_DXFER_FROM_DEV = -3
SG_DXFER_TO_FROM_DEV = -3
SG_DXFER_UNKNOWN = -5

SG_IO = 0x2285


STATUS_SUCCESS = 0x0
STATUS_CHECK_CONDITION = 0x2
STATUS_CONDITION_MET = 0x4
STATUS_BUSY = 0x8
STATUS_INTERMEDIATE = 0x10
STATUS_INTERMEDIATE_COND_MET = 0x14
STATUS_RESERVATION_CONFLICT = 0x18
STATUS_COMMAND_TERMINATED = 0x22
STATUS_QUEUE_FULL = 0x28

SENSE_NONE = 0x0
SENSE_RECOVERED_ERROR = 0x1
SENSE_NOT_READY = 0x2
SENSE_MEDIUM_ERROR = 0x3
SENSE_HARDWARE_ERROR = 0x4
SENSE_ILLEGAL_REQUEST = 0x5
SENSE_UNIT_ATTENTION = 0x6
SENSE_DATA_PROTECT = 0x7
SENSE_BLANK_CHECK = 0x8
SENSE_VENDOR_SPECIFIC = 0x9
SENSE_COPY_ABORTED = 0xa
SENSE_ABORTED_COMMAND = 0xb
SENSE_EQUAL = 0xc
SENSE_VOLUME_OVERFLOW = 0xd
SENSE_MISCOMPARE = 0xe
SENSE_RESERVED = 0xf


def get_status_string(status):
    if status == STATUS_SUCCESS:
        return 'SUCCESS'
    elif status == STATUS_CHECK_CONDITION:
        return 'CHECK_CONDITION'
    elif status == STATUS_CONDITION_MET:
        return 'CONDITION_MET'
    elif status == STATUS_BUSY:
        return 'BUSY'
    elif status == STATUS_INTERMEDIATE:
        return 'INTERMEDIATE'
    elif status == STATUS_INTERMEDIATE_COND_MET:
        return 'INTERMEDIATE_CONDITION_MET'
    elif status == STATUS_RESERVATION_CONFLICT:
        return 'RESERVATION_CONFLICT'
    elif status == STATUS_COMMAND_TERMINATED:
        return 'COMMAND_TERMINATED'
    elif status == STATUS_QUEUE_FULL:
        return 'QUEUE_FULL'
    else:
        return 'UNKNOWN'


class ScsiError(Exception):
    def __init__(self, status):
        msg = 'SCSI error: %s (%d)' % (get_status_string(status), status)
        Exception.__init__(self, msg)
        self.status = status


class CheckConditionError(ScsiError):
    def __init__(self, sense):
        ScsiError.__init__(self, STATUS_CHECK_CONDITION)
        self.sense = sense

    def __str__(self):
        s = 'SCSI CHECK_CONDITION error'
        if not self.sense:
            return s

        s += ':\n  '
        s += '\n  '.join(self.__formatSenseBuf())
        return s

    def __formatSenseBuf(self):
        pass
        out = []
        for x in range(128):
            if (x * 16) >= len(self.sense):
                break
            row = ['%04x:' % (x * 16,)]
            for y in range(16):
                if y == 8:
                    row.append('')
                idx = (x * 16) + y
                if idx >= len(self.sense):
                    break
                row.append('%02x ' % (ord(self.sense[idx]),))
            out.append(' '.join(row))

        return out


class SgIoHdr(ctypes.Structure):
    """
    sg_io_hdr_t

    Defined in "scsi/sg.h"
    """
    _fields_ = [
        # [i] 'S' for SCSI generic (required)
        ('interface_id', ctypes.c_int),
        # [i] data transfer direction
        ('dxfer_direction', ctypes.c_int),
        # [i] SCSI command length ( <= 16 bytes)
        ('cmd_len', ctypes.c_ubyte),
        # [i] max length to write to sbp
        ('mx_sb_len', ctypes.c_ubyte),
        # [i] 0 implies no scatter gather
        ('iovec_count', ctypes.c_ushort),
        # [i] byte count of data transfer
        ('dxfer_len', ctypes.c_uint),
        # [i], [*io] points to data transfer memory or scatter gather list
        ('dxferp', ctypes.c_void_p),
        # [i], [*i] points to command to perform
        ('cmdp', ctypes.c_void_p), # really an "unsigned char *"
        # [i], [*o] points to sense_buffer memory
        ('sbp', ctypes.c_void_p), # really an "unsigned char *"
        # [i] MAX_UINT->no timeout (unit: millisec)
        ('timeout', ctypes.c_uint),
        # [i] 0 -> default, see SG_FLAG...
        ('flags', ctypes.c_uint),
        # [i->o] unused internally (normally)
        ('pack_id', ctypes.c_int),
        # [i->o] unused internally
        ('usr_ptr', ctypes.c_void_p),
        # [o] scsi status
        ('status', ctypes.c_ubyte),
        # [o] shifted, masked scsi status
        ('masked_status', ctypes.c_ubyte),
        # [o] messaging level data (optional)
        ('msg_status', ctypes.c_ubyte),
        # [o] byte count actually written to sbp
        ('sb_len_wr', ctypes.c_ubyte),
        # [o] errors from host adapter
        ('host_status', ctypes.c_ushort),
        # [o] errors from software driver
        ('driver_status', ctypes.c_ushort),
        # [o] dxfer_len - actual_transferred
        ('resid', ctypes.c_int),
        # [o] time taken by cmd (unit: millisec)
        ('duration', ctypes.c_uint),
        # [o] auxiliary information
        ('info', ctypes.c_uint),
    ]

    def describe(self):
        s = []
        for field in self._fields_:
            if field[0] == 'cmdp':
                s.append('cmd:')
                self.__describeBuf(s, self.cmdp, self.cmd_len)
            elif field[0] == 'sbp':
                s.append('sbp:')
                self.__describeBuf(s, self.sbp, self.sb_len_wr)
            else:
                s.append('%s: %s' % (field[0], getattr(self, field[0])))
        return '\n'.join(s)

    def __describeBuf(self, s, ptr, len):
        if ptr is None:
            return s.append('  <null>')
        p = ptr
        end = ptr + len

        while p < end:
            row = []
            for i in range(16):
                if i == 8:
                    row.append('')

                cp = ctypes.cast(p, ctypes.POINTER(ctypes.c_ubyte))
                row.append('%02x' % (cp.contents.value,))

                p += 1
                if p >= end:
                    break

            s.append('  ' + ' '.join(row))


_libc = None
def _get_libc():
    global _libc
    if _libc is None:
        _libc = ctypes.cdll.LoadLibrary('libc.so.6')
    return _libc


def call_sg_io(fd, sg_io_hdr):
    libc = _get_libc()
    libc.ioctl(fd, SG_IO, ctypes.pointer(sg_io_hdr))


def sg_cmd(fd, direction, cmd, dxfer, sense_len=0xff, timeout=5000):
    # Set up the sg_io_hdr_t
    sg_io_hdr = SgIoHdr()
    sg_io_hdr.interface_id = ord('S')
    sg_io_hdr.dxfer_direction = direction

    cmd_len = ctypes.sizeof(cmd)
    if cmd_len > 0xff:
        raise ValueError('command length too large: %d > 0xff' % (cmd_len,))
    sg_io_hdr.cmd_len = cmd_len
    sg_io_hdr.cmdp = ctypes.cast(ctypes.pointer(cmd), ctypes.c_void_p)

    sg_io_hdr.dxfer_len = ctypes.sizeof(dxfer)
    sg_io_hdr.dxferp = ctypes.cast(ctypes.pointer(dxfer), ctypes.c_void_p)

    if sense_len <= 0:
        sg_io_hdr.mx_sb_len = 0
        sense = None
    elif sense_len <= 0xff:
        sg_io_hdr.mx_sb_len = sense_len
        sense = cbuf.CBuffer(sense_len)
        sg_io_hdr.sbp = ctypes.cast(ctypes.pointer(sense.buf), ctypes.c_void_p)
    else:
        raise ValueError('sense length too large: %d > 0xff' % (sense_len,))

    sg_io_hdr.timeout = timeout

    # Make the actual SG_IO call
    call_sg_io(fd, sg_io_hdr)

    # Raise an exception if the status is not STATUS_SUCCESS
    if sg_io_hdr.status == STATUS_CHECK_CONDITION:
        if sense is not None:
            sense_buf = sense[0:sg_io_hdr.sb_len_wr]
        else:
            sense_buf = None
        raise CheckConditionError(sense_buf)
    elif sg_io_hdr.status != STATUS_SUCCESS:
        raise ScsiError(sg_io_hdr.status)
