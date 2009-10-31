#!/usr/bin/python -tt

from .. import cdrom


def get_cddb_id(disc_toc):
    checksum = long(0)
    for track_info in disc_toc.tracks:
        offset = track_info.address.lba + cdrom.MSF_OFFSET
        seconds = offset / cdrom.FRAMES_PER_SECOND
        while seconds > 0:
            checksum = checksum + (seconds % 10)
            seconds = seconds / 10

    last_session = disc_toc.sessions[-1]
    total_secs = ((last_session.leadout.lba / cdrom.FRAMES_PER_SECOND) -
                  (disc_toc.tracks[0].address.lba / cdrom.FRAMES_PER_SECOND))
    disc_id = ((checksum % 0xff) << 24 | total_secs << 8 |
                len(disc_toc.tracks))
    return disc_id
