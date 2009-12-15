#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import datetime
import new

from .field_types import *

g_fields = {}
g_field_sort_key = 0


def NewField(name, parent, field_name, field_doc, album_wide=False, **kw):
    """
    Returns a new Field sub-class.

    Lets us define new field classes with a short call to NewField(),
    rather than manually declaring the class and having to write a bunch of
    common boilerplate code (mainly __init__).
    """
    # Create an __init__ method that takes no arguments (other than self),
    # and passes the field name to the parent (Field) __init__ method.
    if not kw.has_key('__init__'):
        kw['__init__'] = lambda self: parent.__init__(self, self.name,
                                                      self.sortKey)

    # Static variables
    kw['__doc__'] = field_doc
    kw['name'] = field_name
    # We keep track of a sort key for each field.
    # Sorting the fields based on the sort key will put them in the
    # same order that they are listed in this file
    global g_field_sort_key
    kw['sortKey'] = g_field_sort_key
    g_field_sort_key += 1
    # Whether or not the field is the same for all tracks on an album
    # (e.g., for fields like the album title, track count, record label, etc)
    kw['albumWide'] = album_wide

    if __name__ == '__main__':
        full_name = name
    else:
        full_name = '.'.join([__name__, name])

    new_class = new.classobj(full_name, (parent,), kw)

    # Setting globals manually is kind of hacky,
    # but it's much more convienient to be able to just say
    # NewField('MyField', ...) instead of MyField = NewField('MyField', ...)
    globals()[name] = new_class
    g_fields[field_name] = new_class


def validate_track_num(self, value):
    # Valid track numbers are from 1 to 99
    # (specified in ECMA 130, section 22.3.3.1)
    #
    # We also allow track 0 to represent the pre-gap before track 1
    if value < 0:
        raise FieldValueError(self, value,
                              'must be greater than or equal to 0')
    if value > 99:
        raise FieldValueError(self, value, 'must be less than 100')

def validate_release_year(self, value):
    # This is just some sanity checking.
    # Maybe we could relax it in case a user really has a strong reason to
    # want to violate these checks.

    # Values before 1900 are almost certainly invalid.
    # (The release year is the year of this album.  The year the song was
    # composed/written should be stored in a separate field.)
    if value < 1900:
        raise FieldValueError(self, value,
                              'a release year earlier than 1900 is unlikely')
    # Values in the future are also unlikely
    if value > datetime.datetime.now().year:
        raise FieldValueError(self, value, 'release year is in the future')


#
# Fields that are constant across an album
#
NewField('AlbumTitle', TitleField, 'album', 'The album title.',
         album_wide=True)
NewField('DiscNumber', IntField, 'discNumber',
         'The disc number, for multi-volume works.',
         album_wide=True)
NewField('DiscCount', IntField, 'discCount',
         'The total number of discs, for multi-volume works.',
         album_wide=True)
NewField('DiscName', TitleField, 'discName',
         'The name of the disc, for multi-volume works.',
         album_wide=True)
NewField('TrackCount', IntField, 'trackCount',
         'The total number of tracks on the disc.',
         album_wide=True, validate=validate_track_num)
NewField('UpcCode', StringField, 'upc',
         'The EAN/UPC code of the disc.',
         album_wide=True) # TODO: add a validate method?
NewField('DiscID', StringField, 'discId',
         'The disc ID or catalog number (usually on the CD spine).',
         album_wide=True)
NewField('ReleaseYear', IntField, 'releaseYear',
         'The year the album was published.',
         album_wide=True, validate=validate_release_year)
NewField('ReleaseDate', StringField, 'releaseDate',
         'The date the album was published.',
         album_wide=True)
# TODO: publisher/record label?

#
# Fields specific to an individual track
#
NewField('TrackTitle', TitleField, 'trackTitle', 'The track title.')
NewField('TrackNumber', IntField, 'trackNumber', 'The track number.',
         validate=validate_track_num)
NewField('OuterTitle', TitleField, 'outerTitle',
         'If this track is a part of a larger work of music, the name of the '
         'larger work.  For example, the name of the symphony if the track is '
         'a single movement from the symphony.')
# TODO: Add field(s) to can track subsections of a track.
#       e.g., movements in a symphony, if the symphony is all in one track.
#       On the physical CD, the movements within a track are often marked with
#       different index values.
NewField('Subtitle', TitleField, 'subtitle', 'The track subtitle.')
NewField('Version', StringField, 'version',
         'This field can be used to differentiate multiple different '
         'versions of a song.  This is frequently used to contain information '
         'about a remix.')
NewField('ISRC', StringField, 'isrc', 'The track ISRC code.')
# TODO: original artist, original album, original release date, etc.
# TODO: opus, key, source work, other?

#
# Fields that are often constant across an album,
# but may be overridden on a per-track basis
#
NewField('Genre', StringListField, 'genre', 'The music genre.')
NewField('ArtistName', TitleField, 'artist', 'The artist name.')
NewField('ArtistSortName', TitleField, 'artistSortName',
         'The name of the artist to use when sorting tracks by artist name.')
NewField('Composer', TitleField, 'composer', 'The song composer.')
# TODO: CD-TEXT has both Composer and Songwriter fields.
NewField('Arranger', TitleField, 'arranger', 'The song arranger.')
NewField('MixArtist', TitleField, 'mixArtist',
         'The artist that made the remix, if different than the artist.')
# TODO: engineer, lyricist, ensemble, etc.
# We could do something complicated like the ID3 TMCL and TIPL fields if we
# really cared.
