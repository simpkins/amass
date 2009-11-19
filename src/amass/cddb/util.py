#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
from .. import cdrom

__all__ = ['get_cddb_id', 'get_disc_length', 'get_total_track_length',
           'get_cddb_offset', 'get_track_offsets']


def get_cddb_id(disc_toc):
    checksum = long(0)
    for offset in get_track_offsets(disc_toc):
        seconds = offset / cdrom.FRAMES_PER_SECOND
        while seconds > 0:
            checksum = checksum + (seconds % 10)
            seconds = seconds / 10

    total_secs = get_total_track_length(disc_toc)
    disc_id = ((checksum % 0xff) << 24 | total_secs << 8 |
                len(disc_toc.tracks))
    return disc_id


def get_disc_length(disc_toc):
    """
    Get the number of seconds from the very start of the disc (including the 2
    second leadout that is not addressable via LBA) to the leadout of the last
    session.

    This is used for the query command.
    """
    last_session = disc_toc.sessions[-1]
    return get_cddb_offset(last_session.leadout.lba) / cdrom.FRAMES_PER_SECOND


def get_total_track_length(disc_toc):
    """
    Get the length of time between the start of the first track
    and the end of the last track.

    This is used when computing the CDDB disc ID.
    """
    # It's pretty dumb that CDDB uses the total disc length in some places,
    # but the sum of the track lengths in other places.
    # (Note: this isn't even really the sum of the track lengths.  For
    # multisession discs, this also includes the lengths of the TOCs for all
    # sessions but the first.)
    last_session = disc_toc.sessions[-1]
    total_secs = ((last_session.leadout.lba / cdrom.FRAMES_PER_SECOND) -
                  (disc_toc.tracks[0].address.lba / cdrom.FRAMES_PER_SECOND))
    return total_secs


def get_cddb_offset(lba):
    # How lame.  CDDB decided to come up with its own (third) addressing
    # scheme.  A CDDB offset is the LBA + 150.  (In, other words, CDDB offset 0
    # corresponds MSF address 0, but otherwise is in sectors, like LBA.)
    return lba + cdrom.MSF_OFFSET


def get_track_offsets(disc_toc):
    return [get_cddb_offset(t.address.lba) for t in disc_toc.tracks]
