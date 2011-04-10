#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import optparse
import os
import sys

from amass import archive
from amass import metadata


def safe_filename(name):
    """
    safe_filename(name) --> name

    Make a string safe for use as a file name.
    """
    # TODO: It would be nice to strip out non-printable characters, or replace
    # them with some dummy character.
    # TODO: Support making the name safe for Windows, too.
    return name.replace('/', '\\')


def get_track_name(track):
    if track.trackTitle.value is None:
        # We often don't know the title for hidden data before the first track
        title = '<unknown>'
    else:
        title = track.trackTitle

    return safe_filename('%02d - %s' % (track.number, title))


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


def process_track_dir(dir, suffix, album):
    if not os.path.isdir(dir):
        return

    info_list = archive.find_track_files(dir, suffix, album)
    rename_files(info_list)


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
    f = open(dir.layout.getMetadataInfoPath(), 'r')
    dir.album.readTracks(f)
    f.close()

    # Rename the audio files
    process_track_dir(dir.layout.getWavDir(), '.wav', dir.album)
    process_track_dir(dir.layout.getFlacDir(), '.flac', dir.album)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
