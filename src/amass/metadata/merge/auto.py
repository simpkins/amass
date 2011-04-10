#!/usr/bin/python -tt
#
# Copyright (c) 2011, Adam Simpkins
#
import os

from ... import cdrom
from ..sources import CddbSource, CdTextSource, IcedaxSource, MbSource


def _load_sources(album_dir):
    sources = []

    # Information read from the CD via icedax
    icedax_dir = album_dir.layout.getIcedaxDir()
    if os.path.isdir(icedax_dir):
        sources.append(IcedaxSource(icedax_dir))

    # CDDB
    cddb_entries = album_dir.getCddbEntries()
    if cddb_entries is not None:
        cddb_idx = 0
        for entry in cddb_entries:
            source = CddbSource(entry, 'CDDB %d' % (cddb_idx,))
            cddb_idx += 1
            sources.append(source)

    # MusicBrainz
    mb_releases = album_dir.getMbReleases()
    if mb_releases is not None:
        mb_idx = 0
        for release_result in mb_releases:
            source = MbSource(release_result, 'MusicBrainz %d' % (mb_idx,))
            mb_idx += 1
            sources.append(source)

    # CD-TEXT
    cdtext_info = album_dir.getCdText()
    if cdtext_info is not None:
        # We only care about the English info for now
        try:
            block = cdtext_info.getBlock(cdrom.cdtext.LANGUAGE_ENGLISH)
        except KeyError:
            block = None

        if block is not None:
            sources.append(CdTextSource(block))

    return sources

def automerge(album_dir):
    sources = _load_sources(album_dir)
    album = album_dir.album

    for track in album.itertracks():
        # Ignore data tracks
        if track.is_data_track:
            continue

        # Update the track with information from all our sources
        for source in sources:
            source.updateTrack(track)

        # For each field, rate the candidate values
        for field in track.fields.itervalues():
            if field.candidates is not None:
                field.candidates.rateCandidates()

                # If the field didn't already have a value set,
                # update it based on the preferred candidate
                if field.value is None:
                    field.set(field.candidates.preferredChoice.value)
