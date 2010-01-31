#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
from . import fields

import re


class TrackInfo(object):
    """
    A class containing all fields for a single track.
    """
    def __init__(self, number):
        # Initialize one member variable for each field defined in
        # metadata.fields
        self.fields = {}
        for (name, field_class) in fields.g_fields.iteritems():
            field = field_class()
            setattr(self, name, field)
            self.fields[name] = field

        # Also add a plain number attribute, to allow easier access to
        # the integer track number (so users don't have to go through the
        # trackNumber field).
        self.number = number



def write(tracks, out):
    for track in tracks:
        out.write('Track %d\n' % (track.number,))
        for field in track.fields.itervalues():
            if field.value is not None:
                out.write('  %s = %r\n' % (field.name, field.value))

def read(data):
    # Accept strings or file-like objects
    if not isinstance(data, (str, unicode)):
        data = data.read()

    track_re = re.compile(r'Track (\d+)')

    tracks = []
    track = None
    for line in data.splitlines():
        m = track_re.match(line)
        if m:
            if track is not None:
                tracks.append(track)
            number = int(m.group(1))
            track = TrackInfo(number)
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
            raise Exception('expected line to be of the form <name> = <value>')

        try:
            field = track.fields[name]
        except KeyError:
            raise Exception('unknown field %r' % (name,))

        field.set(eval(value))

    if track is not None:
        tracks.append(track)

    return tracks
