#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
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
