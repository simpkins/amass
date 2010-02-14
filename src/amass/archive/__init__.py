#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import errno
import io
import os
import re

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


class FileInfo(object):
    def __init__(self, path, metadata):
        self.path = path
        self.metadata = metadata

    @property
    def name(self):
        return os.path.basename(self.path)


def find_track_files(dir, suffix, tracks):
    """
    Find all files in the specified directory whose name ends with the
    specified suffix.

    All of these files should be audio tracks.  Return a list of FileInfo
    objects, which map the files found to the track metadata.  The tracks
    argument is the list of track metadata to use.
    """
    # Find all files with a matching suffix
    files = []
    for entry in os.listdir(dir):
        if not entry.endswith(suffix):
            continue
        files.append(entry)

    # Try to determine which file corresponds to which track
    #
    # We currently expect an exact 1:1 mapping
    #
    # TODO: At the moment, we look only at the filename.
    # We should also support looking at the file metadata, if present
    numbers_to_name = {}
    info_list = []
    for filename in files:
        # Find all numbers in the filename
        numbers = [int(n) for n in re.findall(r'\d+', filename)]
        # Prune out numbers that aren't in the expected track number range
        numbers = [n for n in numbers if 0 < n and n <= len(tracks)]

        # TODO: For now, we require there to be exactly 1 number in each name.
        # This certainly won't be good enough in the future.  We should detect
        # patterns in the names, to try and figure out where the track number
        # is.  (e.g., the number always comes at the very beginning, or always
        # comes after the artist name, etc.)
        if not numbers:
            raise Exception('no track number found in filename %r' %
                            (filename,))
        if len(numbers) != 1:
            raise Exception('multiple possible track numbers found in '
                            'filename %r: %s' % (filename, numbers))

        # Make sure there are no duplicates
        number = numbers[0]
        if numbers_to_name.has_key(number):
            raise Exception('multiple files found for track number %d: '
                            '%r and %r' %
                            (number, numbers_to_name[number], filename))

        numbers_to_name[number] = filename

        path = os.path.join(dir, filename)
        track = tracks[number - 1]
        info_list.append(FileInfo(path, track))

    # Sort info_list by track numberj
    info_list.sort(key = lambda t: t.metadata.number)
    return info_list
