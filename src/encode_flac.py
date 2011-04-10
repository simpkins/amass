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
from amass import flac


def flac_encode(wav_path, flac_path):
    flac_options = ['-V']
    cmd = ['flac'] + flac_options + ['-o', flac_path, wav_path]
    print 'Encoding %s' % (flac_path,)
    subprocess.check_call(cmd)


def main(argv):
    # Parse the command line options
    usage = '%prog [options] DIR'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--no-tag',
                      action='store_false', dest='tag', default=True,
                      help='Do not tag the flac files')
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
    if options.tag:
        with open(dir.layout.getMetadataInfoPath(), 'r') as f:
            dir.album.readTracks(f)

        info_list = archive.util.find_track_files(dir.layout.getWavDir(),
                                                  '.wav', dir.album)
    else:
        wav_files = file_util.find_files_by_suffix(dir.layout.getWavDir(),
                                                   '.wav')
        info_list = [archive.util.FileInfo(path, None)
                     for path in sorted(wav_files)]

    flac_dir = dir.layout.getFlacDir()
    try:
        os.makedirs(flac_dir)
    except OSError, ex:
        if ex.errno != errno.EEXIST:
            raise

    for info in info_list:
        wav_path = info.path
        (base, suffix) = os.path.splitext(os.path.basename(wav_path))
        assert suffix == '.wav'
        flac_path = os.path.join(flac_dir, base + '.flac')
        flac_encode(wav_path, flac_path)
        if info.metadata is not None:
            flac.tag_file(flac_path, info.metadata)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
