#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import errno
import itertools
import os
import re

from . import track


class Album(object):
    def __init__(self, toc):
        # A cdrom.FullTOC() object
        self.toc = toc

        # An array of track metadata objects.
        # The index corresponds exactly to the track number.
        # (tracks[1] contains info for track 1, tracks[2] for track 2, etc.)
        #
        # If the first track number is not 1, the leading tracks will be set to
        # None.  E.g., if the CD starts with track 3, self.__tracks[1], and
        # self.__tracks[2] will be set to None.
        #
        # If the CD contains "hidden" audio data before the first track, the
        # metadata for that is stored in __tracks[0].  Otherwise, __tracks[0]
        # is set to None.
        self.__tracks = []

        self.__initializeTracks()

    def __initializeTracks(self):
        assert not self.__tracks

        # Initialize self.__tracks[0], based on whether or not there is a
        # hidden audio track after the pre-gap and before the first track.
        if self.toc.hasAudioTrack0():
            self.__tracks.append(track.TrackInfo(0))
        else:
            self.__tracks.append(None)

        # The CD should normally have at least 1 track.
        # However, handle the case when there are no tracks, just in case.
        if not self.toc.tracks:
            return

        # Pad self.__tracks with None, up to the first track number
        for index in range(1, self.toc.tracks[0].number):
            self.__tracks.append(None)

        # Add a TrackInfo object for each track
        index = self.toc.tracks[0].number
        for track_info in self.toc.tracks:
            self.__tracks.append(track.TrackInfo(track_info.number))
            # Assert that all the tracks are consecutive.
            # (This is required by the Red Book)
            assert track_info.number == index
            index += 1

    def track(self, number):
        """
        Get the metadata for the specified track.

        Raises an IndexError if the specified number is invalid.

        If this CD has hidden audio data before the first track, the metadata
        for this data can be accessed by using track number 0.  (An IndexError
        is raise if track number 0 is specified and the CD does not contain
        hidden data before the first track.)
        """
        track_info = self.__tracks[number]
        if track_info is None:
            raise IndexError(number)
        return track_info

    def itertracks(self):
        return itertools.ifilter(lambda x: x is not None, self.__tracks)

    def getFirstTrack(self):
        # TODO: Should this avoid returning track[0] if it exists?
        i = self.itertracks()
        return i.next()

    def writeTracks(self, out):
        for track in self.itertracks():
            out.write('Track %d\n' % (track.number,))
            for field in track.fields.itervalues():
                if field.value is not None:
                    out.write('  %s = %r\n' % (field.name, field.value))

    def readTracks(self, data):
        # Accept strings or file-like objects
        if not isinstance(data, (str, unicode)):
            data = data.read()

        track_re = re.compile(r'Track (\d+)')

        track = None
        for line in data.splitlines():
            m = track_re.match(line)
            if m:
                number = int(m.group(1))
                track = self.track(number)
                continue

            if not line or line.startswith('#'):
                continue

            if not line.startswith('  '):
                raise Exception('expected line to start with 2 spaces')

            if track is None:
                raise Exception('data before first track start')

            try:
                name, value = line.split(' = ', 1)
                name = name.strip()
            except ValueError:
                raise Exception('expected line to be of the form '
                                '<name> = <value>')

            try:
                field = track.fields[name]
            except KeyError:
                raise Exception('unknown field %r' % (name,))

            field.set(eval(value))
