#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import optparse
import sys

from amass import archive
from amass import flac


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

    flac_dir = dir.layout.getFlacDir()
    suffix = '.flac'
    info_list = archive.util.find_track_files(flac_dir, suffix, dir.album)
    for info in info_list:
        print info.path
        flac.tag_file(info.path, info.metadata)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
