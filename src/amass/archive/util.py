#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import os
import re


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
