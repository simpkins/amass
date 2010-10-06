#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import optparse
import os
import subprocess
import sys

from amass import archive
from amass import metadata


def get_vorbis_name(field):
    if field.name == 'album':
        return 'ALBUM'
    if field.name == 'artist':
        return 'ARTIST'
    if field.name == 'trackTitle':
        return 'TITLE'
    if field.name == 'trackNumber':
        return 'TRACKNUMBER'
    if field.name == 'trackCount':
        return 'TRACKTOTAL'
    if field.name == 'discNumber':
        return 'DISCNUMBER'
    if field.name == 'discCount':
        return 'DISCTOTAL'
    if field.name == 'releaseYear':
        return 'DATE'
    if field.name == 'genre':
        return 'GENRE'
    if field.name == 'upc':
        return 'PRODUCTNUMBER'
    if field.name == 'mcn':
        return 'CATALOGNUMBER'
    if field.name == 'isrc':
        return 'ISRC'

    return None


def update_comments(comments, name, value):
    if isinstance(value, (list, tuple)):
        for x in value:
            update_comments(comments, name, x)
    elif isinstance(value, unicode):
        comments.append((name, value))
    elif isinstance(value, (int, long)):
        comments.append((name, unicode(value)))
    else:
        raise NotImplementedError('no support for encoding vorbis comment '
                                  'from value type %s' %
                                  (value.__class__.__name__,))

def tag_files(info_list):
    # Compute the new names for each track
    for info in info_list:
        print info.path
        comments = []

        # Set all of the metadata fields
        for field in info.metadata.fields.itervalues():
            if field.value is None:
                continue

            vorbis_name = get_vorbis_name(field)
            if vorbis_name is None:
                print '  <ignored> %s: %s' % (field.name, field.value)
                continue

            update_comments(comments, vorbis_name, field.value)

        # Set TRACKNUMBER
        comments.append(('TRACKNUMBER', '%d' % (info.metadata.number,)))


        # FIXME: We probably don't want to remove stuff like
        # ReplayGain tags.
        cmd = ['metaflac', '--remove-all-tags']
        for (name, value) in comments:
            print '  %s=%s' % (name, value)
            cmd.append('--set-tag=%s=%s' % (name, value))
        cmd.append(info.path)
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

    # Load the metadata
    f = open(dir.layout.getMetadataInfoPath(), 'r')
    dir.album.readTracks(f)
    f.close()

    flac_dir = dir.layout.getFlacDir()
    suffix = '.flac'
    info_list = archive.util.find_track_files(flac_dir, suffix, dir.album)
    tag_files(info_list)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
