#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import os
import re

from .. import cdrom


class FileInfo(object):
    def __init__(self, path, metadata):
        self.path = path
        self.metadata = metadata

    @property
    def name(self):
        return os.path.basename(self.path)


def find_track_files(dir, suffix, album):
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
        numbers = set([int(n) for n in re.findall(r'\d+', filename)])

        # Prune out numbers that aren't valid track numbers for this album
        possible_numbers = []
        for number in numbers:
            if number == 0:
                if not album.toc.hasAudioTrack0():
                    continue
                track1 = album.toc.getTrack(1)
                track_len = track1.address - cdrom.Address(0, 2, 0)
            else:
                try:
                    track = album.toc.getTrack(number)
                except IndexError:
                    continue
                track_len = track.endAddress - track.address

            # TODO: Check the length of this file, and use it to help
            # guess if it this file is a good match for this track.
            possible_numbers.append(number)

        # TODO: For now, we require there to be exactly 1 number in each name.
        # This certainly won't be good enough in the future.  We should detect
        # patterns in the names, to try and figure out where the track number
        # is.  (e.g., the number always comes at the very beginning, or always
        # comes after the artist name, etc.)
        if not possible_numbers:
            raise Exception('no track number found in filename %r' %
                            (filename,))
        if len(possible_numbers) != 1:
            raise Exception('multiple possible track numbers found in '
                            'filename %r: %s' % (filename, possible_numbers))

        # Make sure there are no duplicates
        number = possible_numbers[0]
        if numbers_to_name.has_key(number):
            raise Exception('multiple files found for track number %d: '
                            '%r and %r' %
                            (number, numbers_to_name[number], filename))

        numbers_to_name[number] = filename

        path = os.path.join(dir, filename)
        track = album.track(number)
        info_list.append(FileInfo(path, track))

    # Sort info_list by track numberj
    info_list.sort(key = lambda t: t.metadata.number)
    return info_list
