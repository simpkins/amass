#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import errno
import optparse
import os
import sys

from amass import cdrom
from amass import cddb
from amass import mb


def fetch_cddb(toc, metadata_dir):
    # Create the cddb directory.
    # For now, just fail if it already exists
    cddb_dir = os.path.join(metadata_dir, 'cddb')
    os.mkdir(cddb_dir)

    # Connect to CDDB, and query for matching discs
    conn = cddb.cddbp.Connection('freedb.freedb.org')
    matches = conn.query(toc)

    # Read each match, and store it in the CDDB directory
    for match in matches:
        buf = conn.read(match.category, match.discId)
        path = os.path.join(cddb_dir, match.category)
        n = 0
        while True:
            if n == 0:
                full_path = path
            else:
                full_path = path + '.' + str(n)

            try:
                fd = os.open(full_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                             0666)
                break
            except OSError, ex:
                if ex.errno != errno.EEXIST:
                    raise

            # Continue, and try another filename
            n += 1

        print 'Writing %s' % (full_path,)
        os.write(fd, buf)
        os.close(fd)


def fetch_mb(toc, metadata_dir):
    # Create the mb directory.
    # For now, just fail if it already exists
    mb_dir = os.path.join(metadata_dir, 'musicbrainz')
    os.mkdir(mb_dir)

    # Query raw data from MusicBrainz
    mb_data = mb.query_toc_raw(toc)

    # Write the response data to a file
    path = os.path.join(mb_dir, 'releases')
    print 'Writing %s' % (path,)

    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0666)
    os.write(fd, mb_data)
    os.close(fd)


def process_dir(dir):
    # Read the table of contents
    toc_path = os.path.join(dir, 'full_toc.raw')
    f = open(toc_path)
    toc_buf = f.read()
    f.close()
    toc = cdrom.FullTOC(toc_buf)

    # Create the metadata directory, if it doesn't already exist
    metadata_dir = os.path.join(dir, 'metadata')
    try:
        os.mkdir(metadata_dir)
    except OSError, ex:
        if ex.errno != errno.EEXIST:
            raise

    fetch_cddb(toc, metadata_dir)
    fetch_mb(toc, metadata_dir)


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

    process_dir(args[0])


if __name__ == '__main__':
    rc = main(sys.argv)
