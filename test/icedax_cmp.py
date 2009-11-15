#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
"""
Examines the current CD via both our internal methods and via icedax,
and makes sure the information reported via both mechanisms agrees.
"""

import optparse
import os
import sys
import traceback

lib_dir = os.path.normpath(os.path.join(sys.path[0], '..', 'src'))
sys.path = [sys.path[0], lib_dir] + sys.path[1:]

from amass import cddb
from amass import cdrom


def check_failure(msg):
    print >> sys.stderr, 'CHECK FAILURE: %s' % (msg,)
    traceback.print_stack(file=sys.stderr)


def check_equal(x, y):
    if x != y:
        check_failure('%r != %r' % (x, y))


def test_track(toc_track, icedax_track):
    # Verify the start address is the same
    check_equal(toc_track.address.lba, icedax_track.getStartSector())

    # TODO: We could also verify the control information.
    # I just haven't written code to parse those icedax fields yet.

    # TODO: We should also parse the binary CD-TEXT info and verify
    # that it matches the info reported by icedax.


def run_test(options):
    # Read the TOC via cdrom
    device = cdrom.binary.Device(options.device)
    toc = cdrom.read_full_toc(device)

    # TODO: Also read CD-TEXT info via cdrom
    #try:
    #    cd_text = cdrom.read_cd_text(device)
    #except cdrom.NoCdTextError:
    #    cd_text_buf = None
    #except cdrom.CdTextNotSupportedError, ex:
    #    warn(str(ex))
    #    cd_text_buf = None
    device.close()

    # Get track information via Icedax
    if options.icedaxDir:
        if not os.path.isdir(options.icedaxDir):
            os.makedirs(options.icedaxDir)
            cdrom.icedax.write_info_files(options.device, options.icedaxDir)

        icedax_tracks = cdrom.icedax.parse_info_dir(options.icedaxDir)
    else:
        icedax_tracks = cdrom.icedax.get_info(options.device)

    # Ensure that the CDDB calculation is the same
    check_equal(cddb.get_cddb_id(toc), icedax_tracks[0].getCddbId())

    # Check each track
    check_equal(len(toc.tracks), len(icedax_tracks))
    for n in range(len(toc.tracks)):
        toc_track = toc.tracks[n]
        icedax_track = icedax_tracks[n]
        test_track(toc_track, icedax_track)


def main(argv):
    usage = '%prog [options]'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-d', '--device', action='store',
                      dest='device', default='/dev/cdrom',
                      metavar='DEVICE', help='The CD-ROM device')
    parser.add_option('-i', '--icedax-dir', action='store',
                      dest='icedaxDir', default=None,
                      metavar='DIR', help='Store/read icedax files from DIR')

    (options, args) = parser.parse_args(argv[1:])

    if args:
        print >> sys.stderr, 'trailing arguments: %s' % (args,)
        parser.print_help(sys.stderr)

    run_test(options)


if __name__ == '__main__':
    rc = main(sys.argv)
