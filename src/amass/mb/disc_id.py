#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import hashlib

import amass.cdrom as cdrom


def _b64encode(binary_disc_id):
    # Slightly non-standard base 64 encoding.
    # . and _ are used as the last two characters (instead of + and /),
    # and '-' is used for padding, instead of '='
    v = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._'
    n = 0
    out = []
    while n < len(binary_disc_id):
        idx = ord(binary_disc_id[n]) >> 2
        out.append(v[idx & 0x3f])

        idx = ord(binary_disc_id[n]) << 4
        if n + 1 < len(binary_disc_id):
            idx += ord(binary_disc_id[n + 1]) >> 4
        out.append(v[idx & 0x3f])

        if n + 1 < len(binary_disc_id):
            idx = ord(binary_disc_id[n + 1]) << 2
            if n + 2 < len(binary_disc_id):
                idx += ord(binary_disc_id[n + 2]) >> 6
            out.append(v[idx & 0x3f])
        else:
            out.append('-')

        if n + 2 < len(binary_disc_id):
            idx = ord(binary_disc_id[n + 2])
            out.append(v[idx & 0x3f])
        else:
            out.append('-')

        n += 3

    return ''.join(out)


def get_mb_id(disc_toc):
    first_track = disc_toc.tracks[0].number

    # MusicBrainz is a little wonky when it comes to computing the end of the
    # disc.  For multisession discs, it calculates the end address as the start
    # of the first track on the last session, minus 11400 sectors.
    #
    # This is intended for CD-XA discs, where there are two sessions, the first
    # containing audio tracks to be played by normal CD players, and the second
    # containing a data track visible to computers.  When there are more than
    # two sessions, the MusicBrainz code still appears to use the start of the
    # last session as the end (not the start of the second, for example).
    if len(disc_toc.sessions) > 1:
        # Find the first track in the last session
        track = disc_toc.getTrack(disc_toc.sessions[-1].firstTrack)
        # Instead of actually retrieving the address lead-out of the
        # next-to-last session, MusicBrainz always uses the start address of
        # the first track in the last session, minus 11400 frames.
        #
        # The 11400 number comes from 6750 frames for the previous session's
        # lead-out (only true if the previous session is the first session),
        # plus 4500 frames for this session's lead-in (not necessarily
        # guaranteed to be 4500, I believe), plus 150 frames of pre-gap.
        end_addr = track.address.lba - 11400

        # Again, instead of retrieving the actual start and end tracks in the
        # last session, MusicBrainz assumes the last session always contains
        # exactly 1 track.
        last_track = disc_toc.tracks[-1].number - 1
    else:
        end_addr = disc_toc.sessions[0].leadout.lba
        last_track = disc_toc.tracks[-1].number

    # Perform the hash calculation.
    # For address offsets, MusicBrainz uses the LBA + 150, just like CDDB
    h = hashlib.sha1()
    h.update('%02X%02X' % (first_track, last_track))
    h.update('%08X' % (end_addr + cdrom.MSF_OFFSET,))
    for n in range(1, 100):
        if n <= last_track:
            offset = disc_toc.getTrack(n).address.lba + cdrom.MSF_OFFSET
        else:
            offset = 0
        h.update('%08X' % (offset,))

    digest = h.digest()
    return _b64encode(digest)
