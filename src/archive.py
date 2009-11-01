#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import optparse
import os
import subprocess
import sys

from amass import cdrom
from amass import cddb


def warn(msg):
    print >> sys.stderr, 'warning: %s' % (msg,)


class Archiver(object):
    def __init__(self, options):
        self.options = options

    def archive(self):
        # Read the TOC and CD-TEXT data
        device = cdrom.binary.Device(self.options.device)
        full_toc_buf = cdrom.binary.read_full_toc(device)
        try:
            cd_text_buf = cdrom.binary.read_cd_text(device)
        except cdrom.NoCdTextError:
            cd_text_buf = None
        except cdrom.CdTextNotSupportedError, ex:
            warn(str(ex))
            cd_text_buf = None
        device.close()

        # Compute the CDDB ID, to use for the output directory name
        self.toc = cdrom.FullTOC(full_toc_buf)
        cddb_id = cddb.get_cddb_id(self.toc)
        self.outputDir = '%08x' % (cddb_id,)
        print 'Archiving CD data to %s%s' % (self.outputDir, os.sep)

        # Note: mkdir may raise an exception,
        # including if a directory with this name already exists.
        os.mkdir(self.outputDir)

        # Store the full toc data
        toc_path = os.path.join(self.outputDir, 'full_toc.raw')
        toc_file = open(toc_path, 'w')
        toc_file.write(full_toc_buf)
        toc_file.close()

        # Store the CD-TEXT data
        if cd_text_buf is not None:
            cd_text_path = os.path.join(self.outputDir, 'cd_text.raw')
            cd_text_file = open(cd_text_path, 'w')
            cd_text_file.write(cd_text_buf)
            cd_text_file.close()

        # Store the track data
        self.archiveTracks()

    def archiveTracks(self):
        # TODO: It would be nice to store the pre-gap and pause information.
        # Although the Mt. Fuji standard says that these
        # areas must be encoded with null information, some audio CD's do hide
        # audio data here:
        # http://en.wikipedia.org/wiki/Pregap#Hidden_audio_tracks
        #
        # If the first track starts later than 00:02:00, I believe we can ask
        # cdparanoia to rip track 0 to get this data.  However, not all CD-ROM
        # drives support reading from the pre-gap.
        #
        # cdparanoia may also rip pause areas in between each track (including
        # them with the previous track).  However, it would be nice if we had
        # some way to indicate which sectors are pause sectors and which are
        # marked as real audio data.
        for track in self.toc.tracks:
            if track.isDataTrack():
                self.archiveDataTrack(track)
            else:
                self.ripAudioTrack(track)

    def archiveDataTrack(self, track):
        print 'Saving data track %d' % (track.number,)
        output_name = 'track%02d.bin' % (track.number,)
        output_path = os.path.join(self.outputDir, output_name)
        cmd = ['readom', 'dev=' + self.options.device,
               'sectors=%d-%d' % (track.address.lba, track.endAddress.lba),
               'f=' + output_path]
        subprocess.check_call(cmd)

    def ripAudioTrack(self, track):
        print 'Ripping audio track %d' % (track.number,)
        output_name = 'track%02d.wav' % (track.number,)
        output_path = os.path.join(self.outputDir, output_name)
        cmd = ['cdparanoia', '-d', self.options.device,
               '--', str(track.number), output_path]
        subprocess.check_call(cmd)


def main(argv):
    parser = optparse.OptionParser()
    parser.add_option('-d', '--device', action='store',
                      dest='device', default='/dev/cdrom',
                      metavar='DEVICE', help='The CD-ROM device')

    (options, args) = parser.parse_args(argv[1:])

    if args:
        print >> sys.stderr, 'trailing arguments: %s' % (args,)
        parser.print_help(sys.stderr)

    archiver = Archiver(options)
    archiver.archive()


if __name__ == '__main__':
    rc = main(sys.argv)
