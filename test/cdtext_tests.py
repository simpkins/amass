#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import os
import sys
import unittest

lib_dir = os.path.normpath(os.path.join(sys.path[0], '..', 'src'))
sys.path = [sys.path[0], lib_dir] + sys.path[1:]

from amass import cdrom
import test_data


class CdTextTests(unittest.TestCase):
    def testWonderWhatsNext(self):
        cd_text = cdrom.cdtext.parse(test_data.CD_TEXT_WONDER_WHATS_NEXT)
        self.assertEqual(len(cd_text.blocks), 1)
        block = cd_text.blocks[0]
        self.assertEqual(block.language, cdrom.cdtext.LANGUAGE_ENGLISH)

        self.assertEqual(block.getTrackTitle(1), 'Family System')
        self.assertEqual(block.getTrackTitle(2), 'Comfortable Liar')
        self.assertEqual(block.getTrackTitle(3), 'Send The Pain Below')
        self.assertEqual(block.getTrackTitle(4), 'Closure')
        self.assertEqual(block.getTrackTitle(5), 'The Red')
        self.assertEqual(block.getTrackTitle(6), "Wonder What's Next")
        self.assertEqual(block.getTrackTitle(7), "Don't Fake This")
        self.assertEqual(block.getTrackTitle(8), 'Forfeit')
        self.assertEqual(block.getTrackTitle(9), 'Grab Thy Hand')
        self.assertEqual(block.getTrackTitle(10), 'An Evening With El Diablo')
        self.assertEqual(block.getTrackTitle(11), 'One Lonely Visitor')

        self.assertEqual(block.getISRC(1), 'US-SM1-02-01527')
        self.assertEqual(block.getISRC(2), 'US-SM1-02-01528')
        self.assertEqual(block.getISRC(3), 'US-SM1-02-01529')
        self.assertEqual(block.getISRC(4), 'US-SM1-02-01530')
        self.assertEqual(block.getISRC(5), 'US-SM1-02-01531')
        self.assertEqual(block.getISRC(6), 'US-SM1-02-01532')
        self.assertEqual(block.getISRC(7), 'US-SM1-02-01533')
        self.assertEqual(block.getISRC(8), 'US-SM1-02-01534')
        self.assertEqual(block.getISRC(9), 'US-SM1-02-01535')
        self.assertEqual(block.getISRC(10), 'US-SM1-02-01536')
        self.assertEqual(block.getISRC(11), 'US-SM1-02-01537')

        self.assertEqual(block.getDiscId(), 'EK86157')
        self.assertEqual(block.getUPC(), '')

    def testGlassworks(self):
        cd_text = cdrom.cdtext.parse(test_data.CD_TEXT_GLASSWORKS)
        self.assertEqual(len(cd_text.blocks), 1)
        block = cd_text.blocks[0]
        self.assertEqual(block.language, cdrom.cdtext.LANGUAGE_ENGLISH)

        self.assertEqual(block.getTrackTitle(1), 'Glassworks: Opening')
        self.assertEqual(block.getTrackTitle(2), 'Glassworks: Floe')
        self.assertEqual(block.getTrackTitle(3), 'Glassworks: Islands')
        self.assertEqual(block.getTrackTitle(4), 'Glassworks: Rubric')
        self.assertEqual(block.getTrackTitle(5), 'Glassworks: Facades')
        self.assertEqual(block.getTrackTitle(6), 'Glassworks: Closing')
        self.assertEqual(block.getTrackTitle(7), 'In The Upper Room: Dance I')
        self.assertEqual(block.getTrackTitle(8), 'In The Upper Room: Dance II')
        self.assertEqual(block.getTrackTitle(9), 'In The Upper Room: Dance V')
        self.assertEqual(block.getTrackTitle(10),
                         'In The Upper Room: Dance VIII')
        self.assertEqual(block.getTrackTitle(11),
                         'In The Upper Room: Dance IX')

        self.assertEqual(block.getTrackTitle(11),
                         'In The Upper Room: Dance IX')

        self.assertEqual(block.getISRC(1), 'USSM18100385')
        self.assertEqual(block.getISRC(2), 'USSM10015213')
        self.assertEqual(block.getISRC(3), 'USSM18100386')
        self.assertEqual(block.getISRC(4), 'USSM18100387')
        self.assertEqual(block.getISRC(5), 'USSM10015214')
        self.assertEqual(block.getISRC(6), 'USSM18100388')
        self.assertEqual(block.getISRC(7), 'USSM18700619')
        self.assertEqual(block.getISRC(8), 'USSM18700620')
        self.assertEqual(block.getISRC(9), 'USSM18700621')
        self.assertEqual(block.getISRC(10), 'USSM18700489')
        self.assertEqual(block.getISRC(11), 'USSM18700622')

        self.assertEqual(block.getDiscId(), 'SK90394')
        self.assertEqual(block.getUPC(), '074643726528')


if __name__ == '__main__':
    unittest.main()
