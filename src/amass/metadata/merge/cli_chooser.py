#!/usr/bin/python -tt
#
# Copyright (c) 2011, Adam Simpkins
#
import sys

from .chooser import ChooserBase


class CliChooser(ChooserBase):
    def __init__(self, album, threshold):
        ChooserBase.__init__(self, album)
        self.confidenceThreshold = threshold

    def write(self, msg):
        if isinstance(msg, unicode):
            msg = msg.encode('utf-8')
        sys.stdout.write(msg)

    def writeln(self, msg):
        self.write(msg)
        sys.stdout.write('\n')

    def writeField(self, track_number, field):
        COLOR_RED = '\033[31m'
        COLOR_YELLOW = '\033[33m'
        COLOR_GREEN = '\033[32m'
        COLOR_RESET = '\033[0m'

        if field.candidates.preferredChoice.confidence < 50:
            conf_color = COLOR_RED
        elif field.candidates.preferredChoice.confidence < 90:
            conf_color = COLOR_YELLOW
        else:
            conf_color = COLOR_GREEN

        fmt_str = (u'{track_number:2} {field.name:<15} '
                   u'{color_conf}'
                   u'{field.candidates.preferredChoice.confidence:3}'
                   u'{color_reset}  '
                   u'{field.candidates.preferredChoice.value}')
        s = fmt_str.format(track_number=track_number, field=field,
                           color_conf=conf_color,
                           color_reset=COLOR_RESET)
        self.writeln(s)

    def choose(self):
        album_wide = self.getAlbumWideFields()

        if album_wide:
            self.writeln('* Album-wide Fields:')
            for field_name in album_wide:
                field = self.album.getFirstTrack().fields[field_name]
                self.writeField('--', field)

        self.writeln('* Track Fields:')

        for track in self.album.itertracks():
            for field in track.fields.itervalues():
                if not field.candidates:
                    continue
                if field.name in album_wide:
                    continue
                if field.name == 'trackNumber':
                    continue
                self.writeField(track.number, field)

        # FIXME: Prompt the user for which fields should be edited
