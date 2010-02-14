#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import errno
import optparse
import os
import subprocess
import sys

from amass import archive
from amass import file_util


def flac_encode(wav_path, flac_path):
    flac_options = ['-V']
    cmd = ['flac'] + flac_options + ['-o', flac_path, wav_path]
    print 'Encoding %s' % (flac_path,)
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

    wav_files = file_util.find_files_by_suffix(dir.getWavDir(), '.wav')
    wav_files.sort()

    flac_dir = os.path.join(dir.path, 'flac')
    try:
        os.makedirs(flac_dir)
    except OSError, ex:
        if ex.errno != errno.EEXIST:
            raise

    for wav_path in wav_files:
        (base, suffix) = os.path.splitext(os.path.basename(wav_path))
        assert suffix == '.wav'
        flac_path = os.path.join(flac_dir, base + '.flac')
        flac_encode(wav_path, flac_path)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
