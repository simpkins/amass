#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#


class ArchiveError(Exception):
    pass


class NotAnAlbumDirError(ArchiveError):
    def __init__(self, path):
        ArchiveError.__init__(self, '%r does not appear to be an album '
                              'directory' % (path,))
        self.path = path
