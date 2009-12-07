#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import errno
import io
import os

from .. import cdrom
from .. import cddb
from .. import mb


class ArchiveError(Exception):
    pass


class NotAnAlbumDirError(ArchiveError):
    def __init__(self, path):
        ArchiveError.__init__(self, '%r does not appear to be an album '
                              'directory' % (path,))
        self.path = path


class AlbumDir(object):
    def __init__(self, path):
        self.path = path
        # Check for a table of contents file,
        # to verify that this looks like an album directory
        if not os.path.isfile(self.getTocPath()):
            raise NotAnAlbumDirError(self.path)

    def getTocPath(self):
        return os.path.join(self.path, 'full_toc.raw')

    def getToc(self):
        toc_path = self.getTocPath()
        try:
            toc_file = open(toc_path, 'rb')
        except OSError, ex:
            if ex.errno == errno.ENOENT:
                raise NotAnAlbumDirError(self.path)
            raise

        toc_buf = toc_file.read()
        toc_file.close()
        return cdrom.FullTOC(toc_buf)

    def getCddbEntries(self):
        cddb_dir = os.path.join(self.path, 'metadata', 'cddb')
        if not os.path.isdir(cddb_dir):
            return None

        entries = []
        for entry in os.listdir(cddb_dir):
            full_path = os.path.join(cddb_dir, entry)

            cddb_file = io.open(full_path, 'r', encoding='UTF-8')
            cddb_buf = cddb_file.read()
            cddb_file.close()

            data = cddb.data.parse(cddb_buf)
            entries.append(data)

        return entries

    def getMbReleases(self):
        releases_path = os.path.join(self.path, 'metadata', 'musicbrainz',
                                     'releases')
        try:
            releases_file = open(releases_path, 'rb')
        except OSError, ex:
            if ex.errno == errno.ENOENT:
                return None
            raise

        release_results = mb.parse_raw_results(releases_file)
        releases_file.close()

        return release_results

    def getCdText(self):
        cdtext_path = os.path.join(self.path, 'cd_text.raw')
        try:
            cdtext_file = open(cdtext_path, 'rb')
            cdtext_buf = cdtext_file.read()
            cdtext_file.close()
        except OSError, ex:
            if ex.errno == errno.ENOENT:
                return None
            raise

        cdtext = cdrom.cdtext.parse(cdtext_buf)
        return cdtext
