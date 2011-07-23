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
from .. import metadata
from . import err


class AlbumDir(object):
    def __init__(self, path, new_toc=None):
        """
        AlbumDir(path, new_toc=None)

        Create a new AlbumDir object.  For existing directories, new_toc should
        be None, and the table of contents will be loaded from the directory.
        When creating a new directory, new_toc should be an amass.cdrom.FullTOC
        object containing the table of contents of the disc.
        """
        self.layout = DirLayout(path)
        if new_toc is None:
            toc = self.__loadToc()
        else:
            toc = new_toc
        self.album = metadata.album.Album(toc)

    def __loadToc(self):
        toc_path = self.layout.getTocPath()
        try:
            toc_file = open(toc_path, 'rb')
        except IOError, ex:
            if ex.errno == errno.ENOENT:
                raise err.NotAnAlbumDirError(self.layout.path)
            raise

        toc_buf = toc_file.read()
        toc_file.close()
        return cdrom.FullTOC(toc_buf)

    def getCddbEntries(self):
        cddb_dir = self.layout.getCddbDir()
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
            releases_file = open(self.layout.getMusicBrainzPath(), 'rb')
        except IOError, ex:
            if ex.errno == errno.ENOENT:
                return None
            raise

        release_results = mb.parse_raw_results(releases_file)
        releases_file.close()

        return release_results

    def getCdText(self):
        try:
            cdtext_file = open(self.layout.getCdTextPath(), 'rb')
            cdtext_buf = cdtext_file.read()
            cdtext_file.close()
        except IOError, ex:
            if ex.errno == errno.ENOENT:
                return None
            raise

        cdtext = cdrom.cdtext.parse(cdtext_buf)
        return cdtext


class DirLayout(object):
    """
    Defines the layout of an album directory.

    This object contains only path information.  It consolidates the directory
    layout in a single location, so that this information is kept separate from
    the rest of the logic.  This makes it easier if we later decide to alter
    the directory layout, or support multiple or configurable directory
    layouts.
    """
    def __init__(self, path):
        self.path = path

    def getMetadataDir(self):
        return os.path.join(self.path, 'metadata')

    def getTocPath(self):
        return os.path.join(self.getMetadataDir(), 'full_toc.raw')

    def getRipLogDir(self):
        return os.path.join(self.getMetadataDir(), 'rip_logs')

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

    def getMp3Dir(self):
        return os.path.join(self.path, 'mp3')
