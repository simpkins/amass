#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
"""
Usage:

    bin2iso ARCHIVE_DIR
    bin2iso TRACK1 OFFSET1 [TRACK2 OFFSET2 ...]

This script converts data tracks from a multisession CD into a single ISO
image.  Ripping a data track from a CD does not produce a valid ISO image,
unless the track was at the very beginning of the CD.  There are two problems:

- Addresses in an ISO file system are relative to the start of the CD.  Ripping
  a data track to a file places the track contents at the start of the file, so
  the offsets from the start of the file are incorrect.

- When mounting a data CD, the operating system looks for the file system
  Volume Descriptor at the beginning of the last session.  For multi-session
  CDs, this is not at the start of the CD.  However, most tools that operate on
  ISO files always look for the Volume Descriptor at the start of the file.

This script overcomes these problems by merging all ripped data tracks into a
single file, placing them at the correct offsets in the file relative to the
start of the CD.  It also copies the Volume Descriptor that was at the start of
the last session to the start of the file.

This results in a sparse file that may appear to be as large as the original
CD, but which only has data where the data tracks exist on the CD.

Benefits and Disadvantages
--------------------------
Instead of using this approach, one could also write a script to update all
offsets in the entire filesystem so that they are relative to the start of the
file.  However, this is trickier to do correctly, since many more locations
need to be updated.  It also won't work if the CD image is using an unknown
extension in the System Area.

The current approach is much simpler, but there are downsides to using sparse
files.  Users may not realize that the file takes up less space on disk than
the actual file size, since many tools aren't good at displaying this
distinction.  Also, if you copy it, many programs will write the full copy out
to disk so that it is no longer sparse.
"""

import optparse
import os
import sys
import shutil

import amass.cdrom
import amass.archive

RETCODE_SUCCESS = 0
RETCODE_ARGUMENTS_ERROR = 1

SECTOR_SIZE = 2048

# The header is the first 17 sectors.
# (The first 16 are the System Area, and next is the Volume
# Descriptor.)
NUM_HEADER_SECTORS = 17
HEADER_SIZE = NUM_HEADER_SECTORS * SECTOR_SIZE


class OptionsError(Exception):
    pass


class UsageError(Exception):
    pass


class OverlapError(Exception):
    def __init__(self, track1, track2):
        Exception.__init__(self, 'tracks %r and %r overlap' %
                           (track1.path, track2.path))
        self.track1 = track1
        self.track2 = track2


class TrackInfo(object):
    def __init__(self, path, offset):
        self.path = path
        self.offset = offset


class Options(optparse.OptionParser):
    def __init__(self):
        optparse.OptionParser.__init__(self, add_help_option = False,
                                        usage = '%prog [options]')
        self.add_option('-o', '--output', action='store',
                        dest='outputPath', default=None, metavar='FILE',
                        help='Write the output ISO image to FILE')
        self.add_option('-h', '--header-track', action='store',
                        dest='headerTrack', default=None, metavar='PATH',
                        help='Use the ISO header from the track specified by '
                        'PATH, instead of the last track specified')
        self.add_option('-?', '--help',
                        action='callback', callback=self.__helpCallback,
                        help='Print this help message and exit')

    def __helpCallback(self, option, opt, value, parser):
        raise UsageError()

    def error(self, msg):
        # This is called automatically by optparse when an error in the command
        # line options is encountered.
        raise OptionsError(msg)

    def printUsage(self, file = sys.stdout):
        self.print_usage(file = file)

    def printHelp(self, file = sys.stdout):
        self.print_help(file = file)

    def __getattr__(self, name):
        # Allow self.__options attributes to be accessed directly
        if name.startswith('__'):
            raise AttributeError(name)
        return getattr(self.__options, name)

    def parseArgv(self, argv):
        # parse the options
        (self.__options, args) = self.parse_args(argv[1:])

        # outputPath is required
        if self.outputPath is None:
            raise OptionsError('no output file specified')

        # Parse the arguments
        self.archiveDir = None
        self.tracks = []
        if not args:
            # Assume the current directory is an archive directory
            self.archiveDir = '.'
        elif len(args) == 1:
            # If a single argument is specified, treat it as the
            # path to an archive directory
            self.archiveDir = args[0]
        elif (len(args) % 2) == 0:
            # If there are two or more args, they should be
            # track, offset pairs
            self.tracks = []
            for n in range(len(args) / 2):
                idx = n * 2
                path = args[idx]
                offset_str = args[idx + 1]
                try:
                    offset = int(offset_str)
                except ValueError:
                    raise OptionsError('invalid track offset %r: '
                                       'must be an integer' % (offset_str,))
                if offset < 0:
                    raise OptionsError('invalid track offset %r: '
                                       'may not be negative' % (offset_str,))
                self.tracks.append(TrackInfo(path, offset))
        else:
            # Hmm.  More than 1 argument, but they don't come in pairs.
            raise OverlapError('odd number of arguments; '
                               'expected track, offset pairs')


def do_tracks_overlap(track1, track2):
    # If necessary, swap track1 and track2 so that
    # track1's offset is less than or equal to track2's
    if track1.offset > track2.offset:
        track1, track2 = track2, track1

    # The tracks overlap iff track1's end is past the start of track2.
    if track1.offset + track1.length > track2.offset:
        return True
    return False


def merge_tracks(output_path, track_list, header_track_path=None):
    # If the header track path is None, treat the last track in the list
    # as the header track
    if header_track_path is None:
        header_track_path = track_list[-1].path
    else:
        # Make sure header_track_path refers to one of the specified tracks
        norm_track_paths = [os.path.normpath(t.path) for t in track_list]
        if os.path.normpath(header_track_path) not in norm_track_paths:
            raise Exception('header track %r is not in the list of '
                            'supplied tracks' % (header_track_path,))

    # Before we start, validate the arguments.
    # Compute the sizes for all of the tracks, and make sure none of them
    # overlap.
    new_track_list = []
    for track in track_list:
        s = os.stat(track.path)
        track.length = s.st_size
        # Make sure there is no overlap with any of
        # the previously processed tracks.
        for track2 in new_track_list:
            if do_tracks_overlap(track, track2):
                raise OverlapError(track, track2)

    # Sort the tracks in order of the offset
    new_track_list.sort(key=lambda t: t.offset)

    # Now begin writing the output file.
    outf = open(output_path, 'wb')

    # Write out each track
    for track_info in track_list:
        inf = open(track_info.path, 'rb')

        # If we are supposed to get the header information from this track,
        # output the track's header to the start of the file.
        if track.path == header_track_path:
            # Read the header sectors from the input file
            header = inf.read(NUM_HEADER_SECTORS * SECTOR_SIZE)

            # Write the header to the start of the file
            outf.seek(0)
            outf.write(header)

            # Write out the track data to the specified offset
            # Manually write the header before calling copyfileobj(), since the
            # inf file pointer is already past it, and we already have it in
            # memory.
            outf.seek(track.offset * SECTOR_SIZE)
            outf.write(header)
            shutil.copyfileobj(inf, outf)
        else:
            # If this track's offset is 0, skip the header, so it doesn't
            # overwrite the header from the selected header track.
            if track.offset < NUM_HEADER_SECTORS:
                # Offset should normally be 0.  It doesn't make much sense
                # For a data track to start partway through the header region.
                # Just skip outputting the first NUM_HEADER_SECTORS sectors.
                inf.seek(NUM_HEADER_SECTORS * SECTOR_SIZE)
                outf.seek((track.offset + NUM_HEADER_SECTORS) * SECTOR_SIZE)
            else:
                outf.seek(track.offset + NUM_HEADER_SECTORS)

            # Copy the track data
            shutil.copyfileobj(inf, outf)

        inf.close()

    outf.close()
    return RETCODE_SUCCESS


def process_archive_dir(output_path, dir):
    toc = dir.album.toc

    track_info_list = []
    for track in toc.tracks:
        if not track.isDataTrack():
            continue
        # We could check to make sure that the track data files actually exist
        # here, but merge_tracks will verify everything before it starts.
        track_path = os.path.join(dir.layout.getDataTrackDir(),
                                  'track%02d.bin' % (track.number,))
        track_info = TrackInfo(track_path, track.address.lba)
        track_info_list.append(track_info)

    header_track_num = toc.sessions[-1].firstTrack
    header_track_path = os.path.join(dir.layout.getDataTrackDir(),
                                     'track%02d.bin' % (header_track_num,))

    return merge_tracks(output_path, track_info_list, header_track_path)


def err_msg(msg):
    print >> sys.stderr, 'error: %s' % (msg,)


def main(argv):
    # Parse the command line options
    options = Options()
    try:
        options.parseArgv(argv)
    except OptionsError, error:
        options.printUsage(sys.stderr)
        err_msg(error)
        return RETCODE_ARGUMENTS_ERROR
    except UsageError, error:
        options.printHelp()
        return RETCODE_SUCCESS

    if options.archiveDir:
        dir = amass.archive.AlbumDir(options.archiveDir)
        return process_archive_dir(options.outputPath, dir)
    else:
        return merge_tracks(options.outputPath, options.tracks)


if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
