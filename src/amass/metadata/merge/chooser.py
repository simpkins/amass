#!/usr/bin/python -tt
#
# Copyright (c) 2011, Adam Simpkins
#


class ChooserBase(object):
    def __init__(self, album):
        if hasattr(album, 'album') and hasattr(album, 'layout'):
            # Accept an AlbumDir objects as well as plain Album objects.
            self.album = album.album
        else:
            self.album = album

    def getAlbumWideFields(self):
        album_wide = []

        track = self.album.getFirstTrack()
        for field in track.fields.itervalues():
            if not field.candidates:
                continue

            all_same = True
            for other_track in self.album.itertracks():
                other_field = other_track.fields[field.name]

                if not other_field.candidates:
                    all_same = False
                    break

                if (field.candidates.preferredChoice.value !=
                    other_field.candidates.preferredChoice.value):
                    all_same = False
                    break

            if all_same:
                album_wide.append(field.name)

        return album_wide
