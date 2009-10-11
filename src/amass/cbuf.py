#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import ctypes


class CBuffer(object):
    """
    A wrapper around a ctypes unsigned byte array.
    """
    def __init__(self, length):
        """
        Create a new CBuffer.

        Accepts a single argument.  If this is an integer, it is treated as the
        buffer length.  If it is a string, the buffer will be initialized from
        the string.
        """
        value = None
        if isinstance(length, str):
            value = length
            length = len(value)

        buftype = ctypes.c_ubyte * length
        self.buf = buftype()
        self.length = length

        if value is not None:
            for n in range(self.length):
                self.buf[n] = ord(value[n])

    def __len__(self):
        return len(self.buf)

    def __getitem__(self, idx):
        """
        Get a byte from the buffer, as a single-byte python string.

        Use getU8() to get the byte as an integer.
        """
        return chr(self.buf[idx])

    def __setitem__(self, idx, value):
        """
        Set a byte in the buffer.

        Accepts either integers or single-byte strings.
        """
        if isinstance(value, str):
            value = ord(value)
        self.buf[idx] = value

    def __getslice__(self, start, end):
        """
        Get a slice of the C buffer, as a python buffer.
        """
        return ''.join([chr(x) for x in self.buf[start:end]])

    def getByteSlice(self, start, end):
        """
        Get a slice of the buffer, as an array of integers.
        """
        return self.buf[start:end]

    def __setslice__(self, start, end, value):
        # We currently don't allow resizing via a slice set.
        # We could support it in the future if  we think the convenience
        # outweighs the downside of making it easier to accidentally do
        # expensive operations.
        if start >= self.length:
            raise ValueError('CBuffer does not allow resizing via slicing')
        if end > self.length:
            end = self.length
        if end - start != len(value):
            print 'start: %r' % (start,)
            print 'end: %r' % (end,)
            raise ValueError('CBuffer does not allow resizing via slicing')

        if isinstance(value, str):
            for n in xrange(end - start):
                self.buf[start + n] = ord(value[n])
        else:
            for n in xrange(end - start):
                self.buf[start + n] = value[n]

    def getU8(self, idx):
        return self.buf[idx]

    def getU16BE(self, offset):
        return (self.buf[offset] << 8) | (self.buf[offset + 1])

    def getU16LE(self, offset):
        return (self.buf[offset + 1] << 8) | (self.buf[offset])

    def getU32BE(self, offset):
        return ((self.buf[offset] << 24) |
                (self.buf[offset + 1] << 16) |
                (self.buf[offset + 2] << 8) |
                (self.buf[offset + 3]))

    def getU32LE(self, offset):
        return ((self.buf[offset + 3] << 24) |
                (self.buf[offset + 2] << 16) |
                (self.buf[offset + 1] << 8) |
                (self.buf[offset]))

    def getU64BE(self, offset):
        return ((self.buf[offset] << 56) |
                (self.buf[offset + 1] << 48) |
                (self.buf[offset + 2] << 40) |
                (self.buf[offset + 3] << 32) |
                (self.buf[offset + 4] << 24) |
                (self.buf[offset + 5] << 16) |
                (self.buf[offset + 6] << 8) |
                (self.buf[offset + 7]))

    def getU64LE(self, offset):
        return ((self.buf[offset + 7] << 56) |
                (self.buf[offset + 6] << 48) |
                (self.buf[offset + 5] << 40) |
                (self.buf[offset + 4] << 32) |
                (self.buf[offset + 3] << 24) |
                (self.buf[offset + 2] << 16) |
                (self.buf[offset + 1] << 8) |
                (self.buf[offset]))
