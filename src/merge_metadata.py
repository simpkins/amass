#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import optparse
import os
import sys

from amass import archive
from amass import cdrom
from amass import file_util
from amass import metadata
from amass.metadata.merge import automerge
from amass.metadata.merge.cli_chooser import CliChooser



def main(argv):
    usage = '%prog [options] DIR'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--dry-run', '-n',
                      action='store_true', dest='dryRun', default=False,
                      help='Dry run only, do not write metadata')
    (options, args) = parser.parse_args(argv[1:])

    if not args:
        parser.print_help(sys.stderr)
        print >> sys.stderr, 'no directory specified'
        return 1
    elif len(args) > 1:
        parser.print_help(sys.stderr)
        print >> sys.stderr, 'trailing arguments: %s' % (args[1:],)
        return 1

    # TODO: If a metadata/info file already exists, take it into account.
    # Its values should probably be pre-selected as the preferred choices for
    # each field.

    dir = archive.AlbumDir(args[0])
    # Automatically select our best guesses
    automerge(dir)

    # Now perform final selection
    chooser = CliChooser(dir, 100)
    chooser.choose()

    if not options.dryRun:
        # NOTE: Since we don't take existing info files into account when
        # performing the merge, we refuse to overwrite any existing file.
        f = file_util.open_new(dir.layout.getMetadataInfoPath())
        dir.album.writeTracks(f)
        f.close()


if __name__ == '__main__':
    rc = main(sys.argv)
