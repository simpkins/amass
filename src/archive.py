#!/usr/bin/python -tt
#
# Copyright (c) 2009-2010, Adam Simpkins
#
import optparse
import sys

from amass import archive
from amass import cddb
from amass import file_util
from amass import mb
from amass import metadata


def main(argv):
    usage = '%prog [options]'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-d', '--device', action='store',
                      dest='device', default='/dev/cdrom',
                      metavar='DEVICE', help='The CD-ROM device')
    parser.add_option('--only', action='store_true',
                      dest='archive_only', default=False,
                      help='Only archive the CD data, do not fetch metadata')

    (options, args) = parser.parse_args(argv[1:])

    if args:
        parser.print_help(sys.stderr)
        print >> sys.stderr, 'trailing arguments: %s' % (args,)
        return 1

    # Save the data off the physical CD
    archiver = archive.Archiver(options.device)
    dir = archiver.archive()

    if options.archive_only:
        return os.EX_OK

    # Fetch metadata information from CDDB and MusicBrainz
    toc = dir.album.toc
    cddb.fetch_cddb(toc, dir)
    mb.fetch_mb(toc, dir)

    # Merge the metadata information
    metadata.merge.automerge(dir)
    chooser = metadata.merge.CliChooser(dir, 100)
    chooser.choose()
    with file_util.open_new(dir.layout.getMetadataInfoPath()) as f:
        dir.album.writeTracks(f)


if __name__ == '__main__':
    rc = main(sys.argv)
