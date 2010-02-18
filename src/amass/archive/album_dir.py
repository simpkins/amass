#!/usr/bin/python -tt
#
# Copyright (c) 2009-2010, Adam Simpkins
#
import errno
import io
import os

from .. import cdrom
from .. import cddb
from .. import mb


class AlbumDir(object):
    def __init__(self, path, new=False):
        self.path = path

        if not new:
            # Check for a table of contents file,
            # to verify that this looks like an album directory
            if not os.path.isfile(self.getTocPath()):
                raise NotAnAlbumDirError(self.path)

    def getMetadataDir(self):
        return os.path.join(self.path, 'metadata')

    def getTocPath(self):
        return os.path.join(self.getMetadataDir(), 'full_toc.raw')

    def getMetadataInfoPath(self):
        return os.path.join(self.getMetadataDir(), 'info')

    def getCdTextPath(self):
        return os.path.join(self.getMetadataDir(), 'cd_text.raw')

    def getIcedaxDir(self):
        return os.path.join(self.getMetadataDir(), 'icedax')

    def getCddbDir(self):
        return os.path.join(self.getMetadataDir(), 'cddb')

    def getMusicBrainzDir(self):
        return os.path.join(self.getMetadataDir(), 'musicbrainz')

    def getMusicBrainzPath(self):
        return os.path.join(self.getMusicBrainzDir(), 'releases')

    def getDataTrackDir(self):
        return os.path.join(self.path, 'data')

    def getWavDir(self):
        return os.path.join(self.path, 'wav')

    def getFlacDir(self):
        return os.path.join(self.path, 'flac')

    def getToc(self):
        toc_path = self.getTocPath()
        try:
            toc_file = open(toc_path, 'rb')
        except IOError, ex:
            if ex.errno == errno.ENOENT:
                raise NotAnAlbumDirError(self.path)
            raise

        toc_buf = toc_file.read()
        toc_file.close()
        return cdrom.FullTOC(toc_buf)

    def getCddbEntries(self):
        cddb_dir = self.getCddbDir()
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
        try:
            releases_file = open(self.getMusicBrainzPath(), 'rb')
        except IOError, ex:
            if ex.errno == errno.ENOENT:
                return None
            raise

        release_results = mb.parse_raw_results(releases_file)
        releases_file.close()

        return release_results

    def getCdText(self):
        try:
            cdtext_file = open(self.getCdTextPath(), 'rb')
            cdtext_buf = cdtext_file.read()
            cdtext_file.close()
        except IOError, ex:
            if ex.errno == errno.ENOENT:
                return None
            raise

        cdtext = cdrom.cdtext.parse(cdtext_buf)
        return cdtext
