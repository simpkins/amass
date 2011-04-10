#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import re
import subprocess
import sys
import time

from . import proc
from . import cdrom


class Ripper(object):
    def __init__(self, device, track_number, output_path, monitor):
        self.device = device
        self.trackNumber = track_number
        self.outputPath = output_path
        self.monitor = monitor

        self.startSector = None
        self.endSector = None

        self.statusRe = re.compile(r'^##: (?P<functionNumber>-?\d+) '
                                   r'\[(?P<functionName>.*)\] @ '
                                   r'(?P<offset>\d+)$')
        self.startSectorRe = re.compile(r'^Ripping from '
                                        r'sector\s+(?P<sector>\d+)')
        self.endSectorRe = re.compile(r'^\s+to sector\s+(?P<sector>\d+)')

    def run(self):
        monitor = proc.ProcLineMonitor(self)
        runner = proc.ProcRunner()

        cmd = ['cdparanoia', '-e', '-d', self.device, '--',
               str(self.trackNumber), self.outputPath]
        process = proc.Proc(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
        runner.run(process, monitor)

    def stdoutLine(self, line):
        # We don't really care about lines printed to stdout.
        # (In general, cdparanoia doesn't print much here when stdout is
        # not a terminal.)
        pass

    def stderrLine(self, line):
        # Check for a status line
        match = self.statusRe.match(line)
        if match:
            # We should see the start and end sector lines before
            # any status output
            assert self.endSector is not None

            self.processStatusLine(match)
            return

        # Check for the lines indicating the start and end sectors
        match = self.startSectorRe.match(line)
        if match:
            self.startSector = int(match.group('sector'))
            return
        match = self.endSectorRe.match(line)
        if match:
            self.endSector = int(match.group('sector'))
            assert self.startSector is not None
            self.monitor.ripStart(self.startSector, self.endSector)
            return

        # Ignore other lines

    def processStatusLine(self, match):
        # The function name indicates what cdparanoia is doing
        # (e.g., "read", "wrote", "verify", etc.)
        function = match.group('functionName')
        # The offset is expressed in number of samples.
        # There are 1176 samples in a sector.
        offset = int(match.group('offset'))

        self.monitor.ripUpdate(function, offset)


class Monitor(object):
    def __init__(self, output):
        self.output = output

        self.startSample = None
        self.endSample = None

        self.readOffset = None
        self.writeOffset = None

        # We currently keep track of the locations of all uncorrected errors
        self.errors = []
        # For warnings, we only track the type of warnings we have seen.
        # On discs with errors, the number of warnings can be extremely high.
        self.warningTypes = set()

        self.numSuppressed = 0
        self.nextWarningTime = 0
        self.suppressionInterval = 5

        self.nextUpdateTime = 0
        self.minUpdateInterval = 0.1

        # Map indicating what to do for each type of cdparanoia status
        self.functionMap = {
            # "read" indicates an offset in the disc where cdparanoia is
            # reading.  The read offset may go backwards, as cdparanoia often
            # re-reads sections of the disc for verification.
            'read' : self.processRead,
            # "verify" indicates that cdparanoia is verifying a run of samples.
            'verify' : None,
            'jitter' : self.processWarning,
            'correction' : self.processWarning,
            'scratch' : self.processWarning,
            'scratch repair' : self.processWarning,
            # "skip" indicates that cdparanoia gave up trying to correct
            # an error
            'skip' : self.processSkip,
            'drift' : self.processWarning,
            'backoff' : self.processWarning,
            # "overlap" indicates that cdparanoia is re-adjusting its read
            # overlap parameter.  The offset is not actual offset, but
            # indicates the new overlap value.  Higher values mean that
            # cdparanoia is seeing more jitter, and so re-reads more data.
            'overlap' : None,
            'dropped' : self.processWarning,
            'duped' : self.processWarning,
            'transport error' : self.processWarning,
            # cdparanoia also treats cache error as a skip
            'cache error' : self.processSkip,
            # "wrote" output indicates an offset of a sample that cdparanoia
            # is writing to the file.  The write offset never decreases.
            'wrote' : self.processWrote,
            # "finished" output indicates that cdparanoia is done
            'finished' : self.processFinished,
        }

    def ripStart(self, start, end):
        self.startSample = start * cdrom.constants.SAMPLES_PER_FRAME
        self.endSample = end * cdrom.constants.SAMPLES_PER_FRAME
        self.output.initialize(self.startSample, self.endSample)
        self.output.log('Ripping from sector %d to %d' % (start, end))

    def ripUpdate(self, function, offset):
        # Multiple handlers check the current time.
        # Compute it once now, rather than potentially having to re-obtain it
        # in multiple places.
        self.now = time.time()

        try:
            handler = self.functionMap[function]
        except KeyError, ex:
            handler = self.processUnknownStatus

        if handler is not None:
            handler(function, offset)

        self.checkSuppressedWarnings()

        if self.now > self.nextUpdateTime:
            self.output.updateSpinner()
            self.output.redisplay()
            # Don't update again until minUpdateInterval has passed
            self.nextUpdateTime = self.now + self.minUpdateInterval

    def processRead(self, function, offset):
        # Keep track of the farthest offset read,
        # and use that to update the progress indicator.
        #
        # (cdparanoia may go back and re-read sectors, and we don't update the
        # progress for those situations.)
        if offset > self.readOffset:
            self.readOffset = offset
            progress_offset = offset
            if progress_offset < self.startSample:
                progress_offset = self.startSample
            elif progress_offset >= self.endSample:
                progress_offset = self.endSample - 1
            self.output.updateProgress(progress_offset)

    def processWrote(self, function, offset):
        # We use the read offsets to update progress; not the write updates.
        # While the write offset is continually increasing, the writes tend
        # to happen in bursts, making it unsuitable to use for the progress
        # indicator.
        #
        # For now, we track the farthest write offset,
        # but we don't use it for anything.
        self.writeOffset = offset

    def processFinished(self, function, offset):
        self.output.finished()

    def processWarning(self, function, offset):
        self.output.warningAt(offset, function)
        self.ripWarning(function, offset)

    def processSkip(self, function, offset):
        self.output.errorAt(offset, function)
        self.ripUncorrectedError(function, offset)

    def processUnknownStatus(self, function, offset):
        self.ripWarning('unknown status %r' % (function,), offset)

    def ripWarning(self, function, offset):
        if function not in self.warningTypes:
            self.warningTypes.add(function)
            self.printSuppressedWarnings()
            self.output.log('warning: %s @ %d' % (function, offset))
        else:
            self.numSuppressed += 1
            self.checkSuppressedWarnings()

    def checkSuppressedWarnings(self):
        if self.numSuppressed == 0:
            return

        if self.now < self.nextWarningTime:
            return
        self.printSuppressedWarnings()

    def printSuppressedWarnings(self):
        self.nextWarningTime = self.now + self.suppressionInterval
        if self.numSuppressed == 0:
            return

        self.output.log('%d similar warnings suppressed' %
                        (self.numSuppressed,))
        self.numSuppressed = 0

    def ripUncorrectedError(self, function, offset):
        self.errors.append((function, offset))
        self.output.log('uncorrected %s @ %d' % (function, offset))


class CliOutput(object):
    STATUS_NORMAL = ' '
    STATUS_WARNING = '*'
    STATUS_UNCORRECTED_ERROR = '!'
    STATUS_READ_HEAD = '>'

    SPINNER_CHARS = r'/-\|'

    def __init__(self):
        self.progressWidth = 60
        self.progressBar = [self.STATUS_NORMAL] * self.progressWidth
        self.spinner_index = 0

    def initialize(self, start, end):
        self.start = start
        self.end = end
        self.currentOffset = start

    def redisplay(self):
        buf = self.progressBar[:]
        buf[self.getIndex(self.currentOffset)] = self.STATUS_READ_HEAD

        spinner = self.SPINNER_CHARS[self.spinner_index]

        sys.stdout.write('%s [%s]\r' % (spinner, ''.join(buf),))
        sys.stdout.flush()

    def updateProgress(self, offset):
        self.currentOffset = offset

    def updateSpinner(self):
        self.spinner_index += 1
        if self.spinner_index >= len(self.SPINNER_CHARS):
            self.spinner_index = 0

    def warningAt(self, offset, type):
        idx = self.getIndex(offset)
        if self.progressBar[idx] == self.STATUS_NORMAL:
            self.progressBar[idx] = self.STATUS_WARNING

    def errorAt(self, offset, type):
        idx = self.getIndex(offset)
        self.progressBar[idx] = self.STATUS_UNCORRECTED_ERROR

    def getIndex(self, offset):
        percent = float(offset - self.start) / float(self.end - self.start)
        return int(percent * self.progressWidth)

    def log(self, message):
        sys.stdout.write('%-78s\n' % (message,))
        self.redisplay()

    def finished(self):
        sys.stdout.write('\n')


def rip_track(device, track_number, output_path):
    output = CliOutput()
    monitor = Monitor(output)
    ripper = Ripper(device, track_number, output_path, monitor)
    ripper.run()

    return (monitor.errors, monitor.warningTypes)
