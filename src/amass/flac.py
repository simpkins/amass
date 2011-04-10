#!/usr/bin/python -tt
#
# Copyright (c) 2011, Adam Simpkins
#
import subprocess


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


def tag_file(path, metadata):
    # Compute the metadata contents
    comments = []

    # Set all of the metadata fields
    for field in metadata.fields.itervalues():
        if field.value is None:
            continue

        vorbis_name = get_vorbis_name(field)
        if vorbis_name is None:
            print '  <ignored> %s: %s' % (field.name, field.value)
            continue

        update_comments(comments, vorbis_name, field.value)

    # Set TRACKNUMBER
    comments.append(('TRACKNUMBER', '%d' % (metadata.number,)))

    # FIXME: We probably don't want to remove stuff like
    # ReplayGain tags.
    cmd = ['metaflac', '--remove-all-tags']
    for (name, value) in comments:
        print '  %s=%s' % (name, value)
        cmd.append('--set-tag=%s=%s' % (name, value))
    cmd.append(path)
    subprocess.check_call(cmd)
