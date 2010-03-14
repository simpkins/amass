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

        # We currently keep track of the locations of all uncorrected errors
        self.errors = []
        # For warnings, we only track the type of warnings we have seen.
        # On discs with errors, the number of warnings can be extremely high.
        self.warningTypes = set()

        self.numSuppressed = 0
        self.nextWarningTime = 0
        self.suppressionInterval = 5

        self.nextProgressTime = 0
        self.progressInterval = 0.1

        # Map indicating what to do for each type of cdparanoia status
        self.functionMap = {
            # "read" indicates an offset in the disc where cdparanoia is
            # reading.  The read offset may go backwards, as cdparanoia often
            # re-reads sections of the disc for verification.
            'read' : None,
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
            # indicates the new overlap value.
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
            'finished' : None,
        }

    def ripStart(self, start, end):
        self.output.log('rip starting: %d - %d' % (start, end))

    def ripUpdate(self, function, offset):
        try:
            handler = self.functionMap[function]
        except KeyError, ex:
            self.processUnknownStatus(function, offset)
            return

        if handler is not None:
            handler(function, offset)

    def processWrote(self, function, offset):
        self.ripProgress(offset)

    def processWarning(self, function, offset):
        self.ripWarning(function, offset)

    def processSkip(self, function, offset):
        self.ripUncorrectedError(function, offset)

    def processUnknownStatus(self, function, offset):
        self.ripWarning('unknown status %r' % (function,), offset)

    def ripProgress(self, offset):
        now = time.time()
        self.checkSuppressedWarnings(now)

        if now > self.nextProgressTime:
            self.output.updateProgress(offset)
            self.nextProgressTime = now + self.progressInterval

    def ripWarning(self, function, offset):
        now = time.time()

        if function not in self.warningTypes:
            self.warningTypes.add(function)
            self.printSuppressedWarnings(now)
            self.output.log('warning: %s @ %d' % (function, offset))
        else:
            self.numSuppressed += 1
            self.checkSuppressedWarnings(now)

    def checkSuppressedWarnings(self, now):
        if self.numSuppressed == 0:
            return

        if now < self.nextWarningTime:
            return
        self.printSuppressedWarnings(now)

    def printSuppressedWarnings(self, now):
        self.nextWarningTime = now + self.suppressionInterval
        if self.numSuppressed == 0:
            return

        self.output.log('%d similar warnings suppressed' %
                        (self.numSuppressed,))
        self.numSuppressed = 0

    def ripUncorrectedError(self, function, offset):
        self.errors.append((function, offset))
        self.output.log('uncorrected %s @ %d' % (function, offset))


class CliOutput(object):
    def __init__(self):
        self.lastProgress = None

    def updateProgress(self, offset):
        self.lastProgress = offset
        assert offset >= self.lastProgress

        sys.stdout.write('%-78s\r' %
                         (offset / cdrom.constants.SAMPLES_PER_FRAME,))
        sys.stdout.flush()

    def log(self, message):
        sys.stdout.write(message)
        sys.stdout.write('\n')

        if self.lastProgress is not None:
            self.updateProgress(self.lastProgress)
        else:
            sys.stdout.flush()


def rip_track(device, track_number, output_path):
    output = CliOutput()
    monitor = Monitor(output)
    ripper = Ripper(device, track_number, output_path, monitor)
    ripper.run()
