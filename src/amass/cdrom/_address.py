#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
__all__ = ['Address']

from .constants import *


class Address(object):
    """
    Represents an address to a sector on the CD-ROM.

    Supports both LBA and MSF addressing schemes.
    """
    def __init__(self, *args, **kwargs):
        if args and kwargs:
            raise TypeError('Address() may not be called with both '
                            'keyword and non-keyword arguments')

        if args:
            if len(args) == 1:
                self.__setFromLBA(args[0])
            elif len(args) == 3:
                self.__setFromMSF(args[0], args[1], args[2])
            else:
                raise TypeError('Address() expects either 1 or 3 '
                                'arguments, not %d' % (len(args),))
        elif kwargs:
            lba = None
            min = None
            sec = None
            frame = None
            for (name, value) in kwargs.iteritems():
                if name == 'lba':
                    lba = value
                elif name == 'min':
                    min = value
                elif name == 'sec':
                    sec = value
                elif name == 'frame':
                    frame = value
                else:
                    raise TypeError('Address() received unexpected keyword '
                                    'argument %r' % (name,))
            if (min is not None or sec is not None or frame is not None):
                if lba is not None:
                    raise TypeError('Address() received both lba and '
                                    'msf-style keyword arguments')
                self.__setFromMSF(min, sec, frame)
            elif lba is not None:
                self.__setFromLBA(lba)
            else:
                # Shouldn't happen, since we have at least 1 keyword arg,
                # and we made sure they were all either lba, min, sec, or
                # frame.
                assert False
        else:
            # No arguments supplied.
            # TODO: Maybe we should set to some default initial value?
            # However, should we use 0, or 2 seconds, since 2s is the
            # first addressable block?
            raise TypeError('Address() requires LBA or MSF arguments')

    def __setFromLBA(self, lba):
        # LBA 0 refers to 2 seconds in
        lba += MSF_OFFSET

        self.frame = lba % FRAMES_PER_SECOND
        self.sec = (lba / FRAMES_PER_SECOND) % SECONDS_PER_MINUTE
        self.min = lba / (FRAMES_PER_SECOND * SECONDS_PER_MINUTE)

    def __setFromMSF(self, min, sec, frame):
        # We accept None instead of 0 for any of these arguments
        # (This allows things like Address(min=3), with specifying
        # sec or frame)
        self.min = min or 0
        self.sec = sec or 0
        self.frame = frame or 0

    def __str__(self):
        return '%02d:%02d.%02d' % (self.min, self.sec, self.frame)

    def __repr__(self):
        return 'Address(%r, %r, %r)' % (self.min, self.sec, self.frame)

    def __eq__(self, addr):
        if not isinstance(addr, Address):
            return False

        if self.frame != addr.frame:
            return False
        if self.sec != addr.sec:
            return False
        if self.min != addr.min:
            return False
        return True

    def __ne__(self, addr):
        return not self.__eq__(addr)

    def __lt__(self, addr):
        value = self.__cmp__(addr)
        if value is NotImplemented:
            return NotImplemented
        return value < 0

    def __le__(self, addr):
        value = self.__cmp__(addr)
        if value is NotImplemented:
            return NotImplemented
        return value <= 0

    def __gt__(self, addr):
        value = self.__cmp__(addr)
        if value is NotImplemented:
            return NotImplemented
        return value > 0

    def __ge__(self, addr):
        value = self.__cmp__(addr)
        if value is NotImplemented:
            return NotImplemented
        return value >= 0

    def __cmp__(self, addr):
        # We define __cmp__ purely for use by the rich comparison operators
        if not isinstance(addr, Address):
            return NotImplemented
        if self.min < addr.min:
            return -3
        elif self.min > addr.min:
            return 3

        if self.sec < addr.sec:
            return -2
        elif self.sec > addr.sec:
            return 2

        if self.frame < addr.frame:
            return -1
        elif self.frame > addr.frame:
            return 1

        return 0

    def __hash__(self):
        return hash(self.min) ^ hash(self.sec) ^ hash(self.frame)

    def __nonzero__(self):
        if self.min == 0 and self.sec == 0 and self.frame == 0:
            return False
        return True

    @property
    def lba(self):
        return ((self.min * SECONDS_PER_MINUTE * FRAMES_PER_SECOND) +
                (self.sec * FRAMES_PER_SECOND) +
                self.frame +
                -MSF_OFFSET)

    @lba.setter
    def lba(self, value):
        self.__setFromLBA(value)
