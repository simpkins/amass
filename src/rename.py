#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import optparse
import os
import re
import sys

from amass import archive
from amass import metadata


class FileInfo(object):
    def __init__(self, path, metadata):
        self.path = path
        self.metadata = metadata

    @property
    def name(self):
        return os.path.basename(self.path)


def find_track_files(dir, suffix, tracks):
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
    paths_to_track = {}
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
        paths_to_track[path] = track

    return paths_to_track


def get_track_name(metadata):
    return '%02d - %s' % (metadata.number, metadata.trackTitle)
    # return 'track%02d' % (metadata.number,)


def rename_files(info_list):
    # Compute the new names for each track
    for info in info_list:
        base, suffix = os.path.splitext(info.path)
        new_name = get_track_name(info.metadata) + suffix

        if new_name == info.name:
            # Already up-to-date
            continue

        old_path = info.path
        new_path = os.path.join(os.path.dirname(info.path), new_name)

        # Make sure nothing exists at the new path,
        # so we'll never blow away an existing file
        if os.path.exists(new_path):
            raise Exception('An file named %r already exists while '
                            'renaming %r' % (new_path, old_path))

        print 'Renaming %r --> %r' % (info.name, new_name)
        os.rename(old_path, new_path)


def main(argv):
    # Parse the command line options
    usage = '%prog [options] DIR'
    parser = optparse.OptionParser(usage=usage)
    (options, args) = parser.parse_args(argv[1:])

    if not args:
        parser.print_help(sys.stderr)
        print >> sys.stderr, 'no directory specified'
        return 1
    elif len(args) > 1:
        parser.print_help(sys.stderr)
        print >> sys.stderr, 'trailing arguments: %s' % (args[1:],)
        return 1

    dir = archive.AlbumDir(args[0])

    # Load the metadata
    f = open(dir.getMetadataInfoPath(), 'r')
    tracks = metadata.track.read(f)
    f.close()

    suffix = '.wav'
    file_map = find_track_files(dir.getWavDir(), suffix, tracks)
    # Convert to a list of TrackInfo objects, sorted by track number
    info_list = [FileInfo(path, track)
                 for (path, track) in file_map.iteritems()]
    info_list.sort(key = lambda t: t.metadata.number)

    rename_files(info_list)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
