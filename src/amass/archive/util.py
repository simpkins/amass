#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import os
import re

from .. import cdrom
from .. import file_util


class FileInfo(object):
    def __init__(self, path, metadata):
        self.path = file_util.decode_path(path)
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
    # First examine all of the filenames, and look for numbers in the name.
    #
    # TODO: At the moment, we look only at the filename.
    # We should also support looking at the file metadata, if present.
    # We should also support looking at the file length, and comparing
    # it with the track lengths from the table of contents
    possible_numbers = {}
    for filename in files:
        # Only examine the base part of the filename.
        # For mp3 files, we don't want to treat the "3" in the extension as a
        # possible track number
        base, ext = os.path.splitext(filename)

        # Find all numbers in the filename
        #
        # TODO  It would be nice to detect patterns in the names, to try and
        # figure out where the track number is.  (e.g., the number always comes
        # at the very beginning, or always comes after the artist name, etc.)
        numbers = set([int(n) for n in re.findall(r'\d+', base)])

        # Prune out numbers that aren't valid track numbers for this album
        possibilities = []
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

            possibilities.append(number)

            if not possibilities:
                raise Exception('no track number found in filename %r' %
                                (filename,))
        possible_numbers[filename] = possibilities

    # Next process the results, and make number to name assignments
    info_list = []
    while possible_numbers:
        # Find a filename that has exactly 1 possibility
        for filename, numbers in possible_numbers.iteritems():
            if len(numbers) == 1:
                break
        else:
            possibilities = ['%s: %s' % (name, numbers)
                             for name, numbers in possible_numbers.iteritems()]
            remaining = '\n  '.join(possibilities)
            raise Exception('unable to determine track numbers for all '
                            'tracks:\n  ' + remaining)

        # TODO: Check the length of this file, and use it to help
        # guess if it this file is a good match for this track.
        number = numbers[0]

        # Remove this filename from the list remaining to be processed
        del possible_numbers[filename]
        # Remove this number from the possibilities for the other tracks
        for (fn, nums) in possible_numbers.iteritems():
            try:
                nums.remove(number)
                if not nums:
                    raise Exception('multiple files found for track number '
                                    '%d: %r and %r' %
                                    (number, filename, fn))
            except ValueError:
                # number wasn't in nums
                pass

        path = os.path.join(dir, filename)
        track = album.track(number)
        info_list.append(FileInfo(path, track))

    # Sort info_list by track numberj
    info_list.sort(key = lambda t: t.metadata.number)
    return info_list
