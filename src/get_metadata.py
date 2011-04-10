#!/usr/bin/python -tt
#
# Copyright (c) 2009-2010, Adam Simpkins
#
import optparse
import sys

from amass import archive
from amass import cddb
from amass import mb


def process_dir(dir):
    toc = dir.album.toc
    cddb.fetch_cddb(toc, dir)
    mb.fetch_mb(toc, dir)


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
