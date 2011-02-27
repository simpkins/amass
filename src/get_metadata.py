#!/usr/bin/python -tt
#
# Copyright (c) 2009-2010, Adam Simpkins
#
import errno
import optparse
import os
import sys

from amass import archive
from amass import cdrom
from amass import cddb
from amass import file_util
from amass import mb


def fetch_cddb(toc, dir):
    # Create the cddb directory.
    # For now, just fail if it already exists
    cddb_dir = dir.layout.getCddbDir()
    os.makedirs(cddb_dir)

    # Query CDDB for entries for this disc
    results = cddb.cddbp.query_cddb(toc)

    # Store each match in the CDDB directory
    for (category, data) in results.iteritems():
        path = os.path.join(cddb_dir, category)
        print 'Writing %s' % (path,)
        data_file = file_util.open_new(path)
        data_file.write(data.encode('UTF-8'))
        data_file.close()


def fetch_mb(toc, dir):
    # Query raw data from MusicBrainz
    mb_data = mb.query_toc_raw(toc)

    mb_path = dir.layout.getMusicBrainzPath()
    print 'Writing %s' % (mb_path,)
    mb_file = file_util.open_new(mb_path)
    mb_file.write(mb_data)
    mb_file.close()


def process_dir(dir):
    toc = dir.album.toc
    fetch_cddb(toc, dir)
    fetch_mb(toc, dir)


def main(argv):
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
    process_dir(dir)


if __name__ == '__main__':
    rc = main(sys.argv)
