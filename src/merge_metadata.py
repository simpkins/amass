#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import optparse
import os
import sys

from amass import archive
from amass import cdrom
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
        tracks = []
        for track in self.toc.tracks:
            mt = self.mergeTrackInfo(track.number)
            tracks.append(mt)

        # FIXME: Add code to allow for human review of the choices.
        # The confidence values should be called out so the reviewer can easily
        # see which fields deserve closer examination.
        for track in tracks:
            print 'Track('
            print '    %r,' % (track.number,)
            for field in track.fields.itervalues():
                if not field.candidates:
                    # Ignore fields with no data sources
                    continue
                field.rateCandidates()
                print('    %s=%r, # confidence = %d%%, score = %d' %
                      (field.name, field.preferredChoice.value,
                       field.preferredChoice.confidence,
                       field.preferredChoice.score))
                if field.preferredChoice.confidence <= 50:
                    print '        # All choices:'
                    for candidate in field.candidates.itervalues():
                        print('        # %r  score=%d, sources=%s' %
                              (candidate.value, candidate.score,
                               candidate.sources))
            print ')'

    def mergeTrackInfo(self, track_number):
        track = metadata.merge.MergeTrack(track_number)
        for source in self.sources:
            source.updateTrack(track)
        return track


def main(argv):
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
    merger = Merger(dir)
    merger.merge()


if __name__ == '__main__':
    rc = main(sys.argv)
