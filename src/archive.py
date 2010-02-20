#!/usr/bin/python -tt
#
# Copyright (c) 2009-2010, Adam Simpkins
#
import optparse
import sys

from amass import archive


def main(argv):
    usage = '%prog [options]'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-d', '--device', action='store',
                      dest='device', default='/dev/cdrom',
                      metavar='DEVICE', help='The CD-ROM device')

    (options, args) = parser.parse_args(argv[1:])

    if args:
        parser.print_help(sys.stderr)
        print >> sys.stderr, 'trailing arguments: %s' % (args,)
        return 1

    archiver = archive.Archiver(options.device)
    archiver.archive()


if __name__ == '__main__':
    rc = main(sys.argv)
