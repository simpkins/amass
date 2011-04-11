#!/usr/bin/python -tt
#
# Copyright (c) 2009-2010, Adam Simpkins
#
import os
import subprocess
import sys

from .. import cdrom
from .. import cddb
from .. import file_util
from .. import notify
from .. import rip

from . import album_dir
from . import err


class Archiver(object):
    def __init__(self, device):
        self.device_name = device

    def archive(self):
        # Read the TOC and CD-TEXT data
        # Note that we close the device after reading this data,
        # so that the track rippers can have exclusive access to the device
        with cdrom.binary.Device(self.device_name) as device:
            full_toc_buf = cdrom.binary.read_full_toc(device)
            try:
                cd_text_buf = cdrom.binary.read_cd_text(device)
            except cdrom.NoCdTextError:
                cd_text_buf = None
            except cdrom.CdTextNotSupportedError, ex:
                notify.warn(str(ex))
                cd_text_buf = None

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
        cdrom.icedax.write_info_files(self.device_name, icedax_dir)

        # Store the track data
        self.archiveTracks()

        return self.outputDir

    def resume(self):
        """
        resume(path)

        Resume archiving an existing directory.  This is useful if archiving
        failed partway on a previous run, and you just want to continue ripping
        the remaining tracks without starting over.

        Currently, this assumes archiving of metadata completed successfully,
        and only the track data archiving needs to be resumed.  Any files that
        are already present on disk will be skipped.  This relies on
        partially-ripped files being deleted before resuming.  (The archiving
        code attempts to remove any partially-ripped files if an error does
        occur, so this usually should do the right thing.)
        """
        # Read the TOC so we can compute the CDDB ID
        with cdrom.binary.Device(self.device_name) as device:
            full_toc_buf = cdrom.binary.read_full_toc(device)
        full_toc = cdrom.FullTOC(full_toc_buf)
        cddb_id = cddb.get_cddb_id(full_toc)

        # Set up our member variables
        self.outputDir = album_dir.AlbumDir('%08x' % (cddb_id,))
        self.toc = self.outputDir.album.toc
        self.layout = self.outputDir.layout

        # Resume archiving the track data
        self.archiveTracks(skip_existing=True)

        return self.outputDir

    def archiveTracks(self, skip_existing=False):
        # If this CD has hidden audio data before the first track,
        # rip it as track 0.
        if self.toc.hasAudioTrack0():
            self.ripAudioTrack0(skip_existing)

        for track in self.toc.tracks:
            if track.isDataTrack():
                self.archiveDataTrack(track, skip_existing)
            else:
                self.ripAudioTrack(track, skip_existing)

    def archiveDataTrack(self, track, skip_existing=False):
        output_name = 'track%02d.bin' % (track.number,)
        output_path = os.path.join(self.layout.getDataTrackDir(),
                                   output_name)
        if self._skip_existing(output_path, skip_existing):
            return
        print 'Saving data track %d' % (track.number,)
        file_util.prepare_new(output_path)
        cmd = ['readom', 'dev=' + self.device_name,
               'sectors=%d-%d' % (track.address.lba, track.endAddress.lba),
               'f=' + output_path]
        try:
            subprocess.check_call(cmd)
        except:
            self._output_failure(output_path)

    def ripAudioTrack(self, track, skip_existing=False):
        # Prepare the output path
        output_name = 'track%02d.wav' % (track.number,)
        output_path = os.path.join(self.layout.getWavDir(), output_name)
        if self._skip_existing(output_path, skip_existing):
            return

        print 'Ripping audio track %d' % (track.number,)
        file_util.prepare_new(output_path)

        # Run the ripper
        output = rip.CliOutput()
        monitor = rip.Monitor(output)
        ripper = rip.Ripper(self.device_name, track.number,
                            output_path, monitor)
        try:
            ripper.run()
        except:
            self._output_failure(output_path)

        # Abort if there were errors
        # Note that we don't remove the output file in this case.
        # We finished ripping to the end of the track, there were just errors
        # trying to accurately rip the data in some sections.  Leave the file
        # around in case the user wants to try and analyze/salvage it.
        if monitor.errors:
            raise err.RipError('%d errors ripping track %d' %
                               (len(monitor.errors), track.number))

    def ripAudioTrack0(self, skip_existing=False):
        output_path = os.path.join(self.layout.getWavDir(), 'track00.wav')
        if self._skip_existing(output_path, skip_existing):
            return
        print 'Ripping hidden audio track 0'

        file_util.prepare_new(output_path)
        # cdparanoia will rip audio data before track 1 by specifying
        # the track number as 0.  It starts ripping just after the pre-gap
        # (MSF 00:02:00, LBA 0), and continues up to the first track.
        cmd = ['cdparanoia', '-d', self.device_name, '--', '0', output_path]
        try:
            subprocess.check_call(cmd)
        except:
            self._output_failure(output_path)

    def _skip_existing(self, path, skip_existing):
        if os.path.exists(path):
            if skip_existing:
                return True
            else:
                raise err.ArchiveError('%s already exists' % (output_path,))
        return False

    def _output_failure(self, path):
        # Save the original exception info
        (ex_type, ex_value, ex_traceback) = sys.exc_info()

        try:
            os.unlink(path)
        except:
            # We're already in the middle of handling an exception,
            # so just ignore the error trying to remove the output file.
            pass

        # Re-raise the original error
        raise ex_type, ex_value, ex_traceback
