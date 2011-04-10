#!/usr/bin/python -tt
#
# Copyright (c) 2011, Adam Simpkins
#
import errno
import optparse
import os
import subprocess
import sys

from amass import archive
from amass import file_util


def get_tag_options(track):
    options = []

    # album, artist, title, year
    fields = {
        'album': '--tl',
        'artist': '--ta',
        'trackTitle': '--tt',
        'releaseYear': '--ty',
    }
    for name, arg in fields.iteritems():
        value = track.fields[name].value
        if value is not None:
            options.append(arg)
            options.append(unicode(value).encode('utf-8'))

    # genre
    genre = track.fields['genre'].value
    if genre:
        # Just use the first genre
        options.extend(['--tg', str(genre[0])])

    # track number
    track_count = track.fields['trackCount'].value
    if track_count is not None:
        tn_arg = '%s/%s' % (track.number, track_count)
    else:
        tn_arg = str(track.number)
    options.extend(['--tn', tn_arg])

    return options

def mp3_encode(wav_path, mp3_path, track_info):
    lame_options = ['-V2', '--add-id3v2']
    lame_options.extend(get_tag_options(track_info))

    cmd = ['lame'] + lame_options + [wav_path, mp3_path]
    print 'Encoding %s' % (mp3_path,)
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

    # Load the track metadata
    f = open(dir.layout.getMetadataInfoPath(), 'r')
    dir.album.readTracks(f)
    f.close()

    # Find the .wav files
    wav_info_list = archive.util.find_track_files(dir.layout.getWavDir(),
                                                  '.wav', dir.album)

    mp3_dir = dir.layout.getMp3Dir()
    try:
        os.makedirs(mp3_dir)
    except OSError, ex:
        if ex.errno != errno.EEXIST:
            raise

    for info in wav_info_list:
        (base, suffix) = os.path.splitext(os.path.basename(info.path))
        assert suffix == '.wav'
        mp3_path = os.path.join(mp3_dir, base + '.mp3')
        mp3_encode(info.path, mp3_path, info.metadata)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
