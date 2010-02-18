#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import os

from .. import cdrom
from . import merge


class Source(object):
    """
    A Source object represents the source of information for album metadata.

    e.g., freedb.org, MusicBrainz, CD-TEXT, etc.
    """
    def __init__(self, name, score=100):
        self.name = name
        self.score = score

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Source(%r)' % (self.name,)


class DataSourceBase(Source):
    """
    A base class for Source classes that contain metadata information.
    """
    def updateTrack(self, track):
        raise NotImplementedError('updateTrack() must be implemented by '
                                  'DataSourceBase subclasses')

    def updateField(self, field, value):
        if field.candidates is None:
            field.candidates = merge.CandidateList(field)
        field.candidates.addCandidate(value, self)


class CddbSource(DataSourceBase):
    """
    A metadata source from a CDDB entry.
    """
    def __init__(self, entry, name, score=None):
        # I haven't been thrilled with the quality of CDDB results in the past.
        # Give CDDB sources a slightly lower score than the default
        if score is None:
            score = 90

        DataSourceBase.__init__(self, name)
        self.entry = entry

    def updateTrack(self, track):
        num = track.number
        self.updateField(track.album, self.entry.getTitle())
        self.updateField(track.trackTitle, self.entry.getTrackTitle(num))
        self.updateField(track.artist, self.entry.getTrackArtist(num))
        self.updateField(track.genre, self.entry.getGenre())
        self.updateField(track.releaseYear, self.entry.getYear())


class MbSource(DataSourceBase):
    """
    A metadata source from a MusicBrainz entry.
    """
    def __init__(self, release_result, name, score=None):
        if score is None:
            # MB scores are between 0 and 100
            # We use this value as-is for now.
            score = release_result.getScore()

        DataSourceBase.__init__(self, name, score)
        self.release = release_result.getRelease()

    def __getTrack(self, track_num):
        offset = self.release.getTracksOffset()
        if offset is None:
            offset = 0

        # Subtract 1, since track 1 is normally at index 0
        # (assuming the offset is 0)
        return self.release.getTracks()[offset + track_num - 1]

    def updateTrack(self, track):
        try:
            mb_track = self.__getTrack(track.number)
        except IndexError:
            # Do nothing if there is no MusicBrainz info for this track
            # (For example, this may occur if this is a data track.)
            return

        self.updateField(track.album, self.release.getTitle())
        self.updateField(track.trackTitle, mb_track.getTitle())

        mb_artist = mb_track.getArtist()
        if mb_artist is None:
            mb_artist = self.release.getArtist()
        self.updateField(track.artist, mb_artist.getName())
        # TODO: make sure the query parameters we send to musicbrainz
        # actually requests that artist sort names be returned.
        self.updateField(track.artistSortName, mb_artist.getSortName())

        try:
            isrcs = mb_track.getISRCs()
        except AttributeError:
            # getISRCs() isn't present in older musicbrainz2 code
            isrcs = []
        for isrc in isrcs:
            self.updateField(track.isrc, isrc)

        # TODO: prefer a US release event:
        for event in self.release.getReleaseEvents():
            # FIXME: Disabled for now since we need more testing
            # - date
            # - catalog number
            # - barcode
            # - label
            pass


class CdTextSource(DataSourceBase):
    """
    A metadata source from a CD-TEXT block.
    """
    def __init__(self, block, score=None):
        if score is None:
            # CD-TEXT information is provided by the publisher.
            # Treat it as more valuable than CDDB or MusicBrainz info.
            # (However, this score still means that if 2 CDDB or MusicBrainz
            # sources agree on a different value, they will be preferred.)
            score = 170
        name = 'CD-TEXT %s' % (cdrom.cdtext.LANGUAGE_NAMES[block.language],)

        DataSourceBase.__init__(self, name, score)
        self.block = block

    def updateTrack(self, track):
        num = track.number
        self.updateField(track.album, self.block.getAlbumTitle())
        self.updateField(track.trackTitle, self.block.getTrackTitle(num))


class IcedaxSource(DataSourceBase):
    """
    A metadata source that represents information extracted from the
    CD via icedax.
    """
    def __init__(self, dir):
        Source.__init__(self, 'CD (via icedax)', 10000)
        self.dir = dir

    def updateTrack(self, track):
        # Load the icedax info from the .inf file
        filename = 'audio_%02d.inf' % (track.number,)
        path = os.path.join(self.dir, filename)
        info = cdrom.icedax.parse_info_file(path)

        # Note that we don't store any information that icedax extracts from
        # CD-TEXT here.  The CdTextSource is used for that purpose.

        # Store the MCN
        try:
            mcn = info.getMCN()
            self.updateField(track.mcn, mcn.decode('ascii'))
        except KeyError:
            # No MCN in icedax info
            pass

        # Store the ISRC info
        try:
            isrc = info.getISRC()
            self.updateField(track.isrc, isrc.decode('ascii'))
        except KeyError:
            # No ISRC in icedax info
            pass
