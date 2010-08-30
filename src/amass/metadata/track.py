#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
from . import fields


class TrackInfo(object):
    """
    A class containing all fields for a single track.
    """
    def __init__(self, number, is_data_track):
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

        self.is_data_track = is_data_track
