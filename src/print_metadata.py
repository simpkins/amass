#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import logging
import optparse
import os
import sys

import amass
from amass import archive
from amass import cdrom


def print_cddb(entry):
    print 'CDDB:'
    print '  Artist: %s' % (entry.getArtist(),)
    print '  Title: %s' % (entry.getTitle(),)


def print_cddb_entries(dir):
    cddb_entries = dir.getCddbEntries()
    for entry in cddb_entries:
        print_cddb(entry)


def print_mb(dir):
    n = 0
    for release_result in dir.getMbReleases():
        n += 1
        print 'MusicBrainz %d: score=%s' % (n, release_result.getScore())
        release = release_result.getRelease()
        print '  Artist: %s' % (release.getArtist().getName(),)
        print '  Title: %s' % (release.getTitle())


def print_cdtext_block(block):
    print('  CD-TEXT Language: %r' %
          (cdrom.cdtext.LANGUAGE_NAMES[block.language],))
    print '    Album: %r' % (block.getAlbumTitle(),)
    print '    Performer: %r' % (block.getPerformer(),)
    print '    Songwriter: %r' % (block.getSongWriter(),)
    print '    Composer: %r' % (block.getComposer(),)
    print '    Arranger: %r' % (block.getArranger(),)
    print '    Message: %r' % (block.getMessage(),)
    print '    Genre: %r' % (block.getGenre(),)
    print '    UPC: %r' % (block.getUPC(),)
    print '    Disc ID: %r' % (block.getDiscId(),)

    first_track, last_track = block.getTrackRange()
    for track_num in range(first_track, last_track + 1):
        print '    Track %d' % (track_num,)
        print '      Title: %r' % (block.getTrackTitle(track_num),)
        print '      ISRC: %r' % (block.getISRC(track_num),)

def print_cdtext(dir):
    print 'CD-TEXT:'

    cdtext = dir.getCdText()
    if cdtext is None:
        print '  No CD-TEXT'
        return

    for block in cdtext.blocks:
        print_cdtext_block(block)



def process_dir(dir):
    print_cddb_entries(dir)
    print_mb(dir)
    print_cdtext(dir)


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

    amass.log.addHandler(logging.StreamHandler(sys.stderr))

    dir = archive.AlbumDir(args[0])
    process_dir(dir)


if __name__ == '__main__':
    rc = main(sys.argv)
