#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import os
import sys
import unittest

lib_dir = os.path.normpath(os.path.join(sys.path[0], '..', 'src'))
sys.path = [sys.path[0], lib_dir] + sys.path[1:]

from amass import album
from amass import cdrom
from amass import metadata
import test_data


class AlbumTests(unittest.TestCase):
    def testTracksGlassworks(self):
        toc = cdrom.FullTOC(test_data.FULL_TOC_GLASSWORKS)
        a = album.Album(toc)

        self.assertRaises(IndexError, a.track, 0)
        for n in range(1, 12):
            track = a.track(n)
            self.assertTrue(isinstance(track, metadata.track.TrackInfo))
        self.assertRaises(IndexError, a.track, 12)

    def testTracksDuskAndSummer(self):
        toc = cdrom.FullTOC(test_data.FULL_TOC_DUSK_AND_SUMMER)
        a = album.Album(toc)

        for n in range(0, 11):
            track = a.track(n)
            self.assertTrue(isinstance(track, metadata.track.TrackInfo))
        self.assertRaises(IndexError, a.track, 11)


if __name__ == '__main__':
    unittest.main()
