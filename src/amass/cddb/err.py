#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
__all__ = ['CddbError', 'NoMatchesError']


class CddbError(Exception):
    pass


class ProtocolError(CddbError):
    pass


class NoMatchesError(ProtocolError):
    def __init__(self, disc_id, category=None):
        msg = 'no CDDB matches found for disc %#x' % (disc_id,)
        if category is not None:
            msg += ' in category %r' % (category,)
        CddbError.__init__(self, msg)
        self.discId = disc_id
        self.category = category
