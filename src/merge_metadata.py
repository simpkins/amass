#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import optparse
import os
import sys

from amass import archive
from amass import cdrom
from amass import file_util
from amass import metadata


class Merger(object):
    def __init__(self, dir):
        self.dir = dir
        self.toc = self.dir.getToc()
        self.sources = self.initSources()

    def initSources(self):
        sources = []

        cddb_entries = self.dir.getCddbEntries()
        if cddb_entries is not None:
            cddb_idx = 0
            for entry in cddb_entries:
                source = metadata.merge.CddbSource(entry,
                                                   'CDDB %d' % (cddb_idx,))
                cddb_idx += 1
                sources.append(source)

        mb_releases = self.dir.getMbReleases()
        if mb_releases is not None:
            mb_idx = 0
            for release_result in mb_releases:
                source = metadata.merge.MbSource(release_result,
                                                 'MusicBrainz %d' % (mb_idx,))
                mb_idx += 1
                sources.append(source)

        self.cdtextSources = []
        cdtext_info = self.dir.getCdText()
        if cdtext_info is not None:
            # We only care about the English info for now
            try:
                block = cdtext_info.getBlock(cdrom.cdtext.LANGUAGE_ENGLISH)
            except KeyError:
                block = None

            if block is not None:
                sources.append(metadata.merge.CdTextSource(block))

        return sources

    def merge(self):
        # Perform initial auto-merge of the data
        tracks = self.createMergeTracks()

        # Now perform final selection
        chooser = CliChooser(tracks, 100)
        chooser.choose()

        # Extract the merged information
        final_tracks = []
        for track in tracks:
            final_tracks.append(track.mergedTrackInfo)

        return final_tracks

    def createMergeTracks(self):
        merge_tracks = []
        for track in self.toc.tracks:
            # Create a new MergeTrack object
            mt = metadata.merge.MergeTrack(track.number)
            final_track = mt.mergedTrackInfo

            # Update the MergeTrack with information from all our sources
            for source in self.sources:
                source.updateTrack(mt)

            # For each field, rate the candidate values
            for field in mt.fields.itervalues():
                field.rateCandidates()

                # Update the final merged track info with the preferred choice.
                # This may later be overridden by one of the chooser methods.
                pref = field.preferredChoice
                if pref is not None:
                    final_track.fields[field.name].set(pref.value)

            merge_tracks.append(mt)

        return merge_tracks


class ChooserBase(object):
    def __init__(self, tracks):
        self.tracks = tracks

    def getAlbumWideFields(self):
        album_wide = []

        track = self.tracks[0]
        for field in track.fields.itervalues():
            if not field.candidates:
                continue

            all_same = True
            for other_track in self.tracks[1:]:
                other_field = other_track.fields[field.name]

                if not other_field.candidates:
                    all_same = False
                    break

                if (field.preferredChoice.value !=
                    other_field.preferredChoice.value):
                    all_same = False
                    break

            if all_same:
                album_wide.append(field.name)

        return album_wide


class CliChooser(ChooserBase):
    def __init__(self, tracks, threshold):
        ChooserBase.__init__(self, tracks)
        self.confidenceThreshold = threshold

    def write(self, msg):
        sys.stdout.write(msg)

    def writeln(self, msg):
        sys.stdout.write(msg)
        sys.stdout.write('\n')

    def writeField(self, track_number, field):
        COLOR_RED = '\033[31m'
        COLOR_YELLOW = '\033[33m'
        COLOR_GREEN = '\033[32m'
        COLOR_RESET = '\033[0m'

        if field.preferredChoice.confidence < 50:
            conf_color = COLOR_RED
        elif field.preferredChoice.confidence < 90:
            conf_color = COLOR_YELLOW
        else:
            conf_color = COLOR_GREEN

        fmt_str = ('{track_number:2} {field.name:<15} '
                   '{color_conf}'
                   '{field.preferredChoice.confidence:3}'
                   '{color_reset}  '
                   '{field.preferredChoice.value}')
        s = fmt_str.format(track_number=track_number, field=field,
                           color_conf=conf_color,
                           color_reset=COLOR_RESET)
        self.writeln(s)

    def choose(self):
        album_wide = self.getAlbumWideFields()

        if album_wide:
            self.writeln('* Album-wide Fields:')
            for field_name in album_wide:
                field = self.tracks[0].fields[field_name]
                # FIXME: there shouldn't be a track number in the output here
                self.writeField('--', field)

        self.writeln('* Track Fields:')

        for track in self.tracks:
            for field in track.fields.itervalues():
                if not field.candidates:
                    continue
                if field.name in album_wide:
                    continue
                if field.name == 'trackNumber':
                    continue
                self.writeField(track.number, field)

        # FIXME: Prompt the user for which fields should be edited


# TODO: Add a GUI chooser, too.


def main(argv):
    usage = '%prog [options] DIR'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--dry-run', '-n',
                      action='store_true', dest='dryRun', default=False,
                      help='Dry run only, do not write metadata')
    (options, args) = parser.parse_args(argv[1:])

    if not args:
        parser.print_help(sys.stderr)
        print >> sys.stderr, 'no directory specified'
        return 1
    elif len(args) > 1:
        parser.print_help(sys.stderr)
        print >> sys.stderr, 'trailing arguments: %s' % (args[1:],)
        return 1

    # TODO: If a metadata/info file already exists, take it into account.
    # Its values should probably be pre-selected as the preferred choices for
    # each field.

    dir = archive.AlbumDir(args[0])
    merger = Merger(dir)
    tracks = merger.merge()

    if not options.dryRun:
        f = file_util.open_new(dir.getMetadataInfoPath())
        metadata.track.write(tracks, f)
        f.close()


if __name__ == '__main__':
    rc = main(sys.argv)
