#!/usr/bin/python -tt
#
# Copyright (c) 2011, Adam Simpkins
#
"""
Decode the flac files in an album directory to re-create the
original .wav files.
"""

import errno
import optparse
import os
import subprocess
import sys

from amass import archive
from amass import file_util
from amass import flac


def flac_decode(flac_path, wav_path):
    cmd = ['flac', '-d', '-o', wav_path, flac_path]
    print 'Decoding %s' % (wav_path,)
    subprocess.check_call(cmd)


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

    # Load the file list
    flac_files = file_util.find_files_by_suffix(dir.layout.getFlacDir(),
                                                '.flac')
    flac_files.sort()

    wav_dir = dir.layout.getWavDir()
    try:
        os.makedirs(wav_dir)
    except OSError, ex:
        if ex.errno != errno.EEXIST:
            raise

    for flac_path in flac_files:
        (base, suffix) = os.path.splitext(os.path.basename(flac_path))
        assert suffix == '.flac'
        wav_path = os.path.join(wav_dir, base + '.wav')
        flac_decode(flac_path, wav_path)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
