#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import os
import sys
import unittest

lib_dir = os.path.normpath(os.path.join(sys.path[0], '..', 'src'))
sys.path = [sys.path[0], lib_dir] + sys.path[1:]

import amass.cdrom

INF_RUSH_2112_TRACK_1="""\
#created by icedax 1.1.9 11/14/09 19:03:31
#
CDINDEX_DISCID=	'QJYSSgL6ukRaRI2NtuExvidlmFk-'
CDDB_DISCID=	0x4f091c06
MCN=		
ISRC=		               
#
Albumperformer=	''
Performer=	''
Albumtitle=	''
Tracktitle=	''
Tracknumber=	1
Trackstart=	0
# track length in sectors (1/75 seconds each), rest samples
Tracklength=	92510, 0
Pre-emphasis=	no
Channels=	2
Copy_permitted=	once (copyright protected)
Endianess=	little
# index list
Index=		0 20440 30450 46147 62802 71810 82395 
Index0=		92467 
"""


class IcedaxTests(unittest.TestCase):
    def test(self):
        info = amass.cdrom.icedax.parse_info_string(INF_RUSH_2112_TRACK_1,
                                                    'audio_01.inf')
        self.assertEqual(info.getNumber(), 1)

        # This CD doesn't have CD-TEXT, so all those fields are empty
        self.assertEqual(info.getTitle(), '')
        self.assertEqual(info.getAlbum(), '')
        self.assertEqual(info.getPerformer(), '')

        self.assertEqual(info.getMCN(), '')
        self.assertEqual(info.getISRC(), '')
        self.assertEqual(info.getCddbId(), 0x4f091c06)

        self.assertEqual(info.getStartSector(), 0)
        self.assertEqual(info.getNumSectors(), 92510)
        self.assertEqual(info.getIndices(), [0, 20440, 30450, 46147,
                                             62802, 71810, 82395])
        self.assertEqual(info.getNextTrackPreGap(), 92467)


if __name__ == '__main__':
    unittest.main()
