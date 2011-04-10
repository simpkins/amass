#!/usr/bin/python -tt
#
# Copyright (c) 2009-2010, Adam Simpkins
#
import os
import subprocess

from .. import cdrom
from .. import cddb
from .. import file_util
from .. import notify
from .. import rip

from . import album_dir
from . import err


class Archiver(object):
    def __init__(self, device):
        self.device = device

    def archive(self):
        # Read the TOC and CD-TEXT data
        device = cdrom.binary.Device(self.device)
        full_toc_buf = cdrom.binary.read_full_toc(device)
        try:
            cd_text_buf = cdrom.binary.read_cd_text(device)
        except cdrom.NoCdTextError:
            cd_text_buf = None
        except cdrom.CdTextNotSupportedError, ex:
            notify.warn(str(ex))
            cd_text_buf = None
        device.close()

        # Compute the CDDB ID, to use for the output directory name
        self.toc = cdrom.FullTOC(full_toc_buf)
        cddb_id = cddb.get_cddb_id(self.toc)

        # Create the album directory
        self.outputDir = album_dir.AlbumDir('%08x' % (cddb_id,), self.toc)
        self.layout = self.outputDir.layout
        print 'Archiving CD data to %s%s' % (self.layout.path, os.sep)

        # Store the full toc data
        toc_file = file_util.open_new(self.layout.getTocPath())
        toc_file.write(full_toc_buf)
        toc_file.close()

        # Store the CD-TEXT data
        if cd_text_buf is not None:
            # Parse the CD-TEXT data to make sure it looks valid.
            # If there was an error reading the data, checksum validation
            # should hopefully fail.
            # TODO: it would be nice to catch the checksum failure and retry to
            # read the data.
            cd_text = cdrom.cdtext.parse(cd_text_buf)

            cd_text_file = file_util.open_new(self.layout.getCdTextPath())
            cd_text_file.write(cd_text_buf)
            cd_text_file.close()

        # TODO: it would be nice to also record which sectors are marked
        # as pause sectors.  Storing the indices is probably sufficient for
        # now, since usually only index 0 is pause.

        # Store extra track information via icedax
        # (This includes things like the locations of the indices and
        # pregap within each track, the ISRC numbers, and the MCN number.)
        print 'Reading track metadata (this may take some time)...'
        icedax_dir = self.layout.getIcedaxDir()
        os.makedirs(icedax_dir)
        cdrom.icedax.write_info_files(self.device, icedax_dir)

        # Store the track data
        self.archiveTracks()

        return self.outputDir

    def archiveTracks(self):
        # If this CD has hidden audio data before the first track,
        # rip it as track 0.
        if self.toc.hasAudioTrack0():
            self.ripAudioTrack0()

        for track in self.toc.tracks:
            if track.isDataTrack():
                self.archiveDataTrack(track)
            else:
                self.ripAudioTrack(track)

    def archiveDataTrack(self, track):
        print 'Saving data track %d' % (track.number,)
        output_name = 'track%02d.bin' % (track.number,)
        output_path = os.path.join(self.layout.getDataTrackDir(),
                                   output_name)
        file_util.prepare_new(output_path)
        cmd = ['readom', 'dev=' + self.device,
               'sectors=%d-%d' % (track.address.lba, track.endAddress.lba),
               'f=' + output_path]
        subprocess.check_call(cmd)

    def ripAudioTrack(self, track):
        print 'Ripping audio track %d' % (track.number,)
        # Prepare the output path
        output_name = 'track%02d.wav' % (track.number,)
        output_path = os.path.join(self.layout.getWavDir(), output_name)
        file_util.prepare_new(output_path)

        # Run the ripper
        output = rip.CliOutput()
        monitor = rip.Monitor(output)
        ripper = rip.Ripper(self.device, track.number, output_path, monitor)
        ripper.run()

        # Abort if there were errors
        if monitor.errors:
            raise err.RipError('%d errors ripping track %d' %
                               (len(monitor.errors), track.number))

    def ripAudioTrack0(self):
        print 'Ripping hidden audio track 0'
        output_path = os.path.join(self.layout.getWavDir(), 'track00.wav')
        file_util.prepare_new(output_path)
        # cdparanoia will rip audio data before track 1 by specifying
        # the track number as 0.  It starts ripping just after the pre-gap
        # (MSF 00:02:00, LBA 0), and continues up to the first track.
        cmd = ['cdparanoia', '-d', self.device, '--', '0', output_path]
        subprocess.check_call(cmd)
