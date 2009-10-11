#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import os
import sys
import unittest

lib_dir = os.path.normpath(os.path.join(sys.path[0], '..', 'src'))
sys.path = [sys.path[0], lib_dir] + sys.path[1:]

from amass import cdrom
import test_data


class FullTocTests(unittest.TestCase):
    def testReencode(self):
        full_toc = cdrom.FullTOC(test_data.FULL_TOC_GLASSWORKS)
        self.assertEqual(test_data.FULL_TOC_GLASSWORKS, full_toc.toBuffer())

    def checkTrack(self, toc, number, session, ctrl, address, end_address):
        track = toc.getTrack(number)
        self.assertEqual(track.number, number)
        self.assertEqual(track.sessionNumber, session)
        self.assertEqual(track.session.number, session)
        self.assertEqual(track.ctrl, ctrl)
        self.assertEqual(track.address, address)
        self.assertEqual(track.endAddress, end_address)

    def testGlassworks(self):
        full_toc = cdrom.FullTOC(test_data.FULL_TOC_GLASSWORKS)
        self.assertEqual(len(full_toc.sessions), 1)
        self.assertEqual(full_toc.sessions[0].number, 1)
        self.assertEqual(full_toc.sessions[0].firstTrack, 1)
        self.assertEqual(full_toc.sessions[0].lastTrack, 11)
        self.assertEqual(full_toc.sessions[0].leadout, cdrom.Address(283575))
        self.assertEqual(full_toc.sessions[0].discType,
                         cdrom.DISC_TYPE_CD)

        self.checkTrack(full_toc, 1, 1, 0,
                        cdrom.Address(0), cdrom.Address(28867))
        self.checkTrack(full_toc, 2, 1, 0,
                        cdrom.Address(28867), cdrom.Address(55830))
        self.checkTrack(full_toc, 3, 1, 0,
                        cdrom.Address(55830), cdrom.Address(90357))
        self.checkTrack(full_toc, 4, 1, 0,
                        cdrom.Address(90357), cdrom.Address(117700))
        self.checkTrack(full_toc, 5, 1, 0,
                        cdrom.Address(117700), cdrom.Address(150790))
        self.checkTrack(full_toc, 6, 1, 0,
                        cdrom.Address(150790), cdrom.Address(178072))
        self.checkTrack(full_toc, 7, 1, 0,
                        cdrom.Address(178072), cdrom.Address(183367))
        self.checkTrack(full_toc, 8, 1, 0,
                        cdrom.Address(183367), cdrom.Address(209050))
        self.checkTrack(full_toc, 9, 1, 0,
                        cdrom.Address(209050), cdrom.Address(224427))
        self.checkTrack(full_toc, 10, 1, 0,
                        cdrom.Address(224427), cdrom.Address(246772))
        self.checkTrack(full_toc, 11, 1, 0,
                        cdrom.Address(246772), cdrom.Address(283575))

    def testKarmacode(self):
        full_toc = cdrom.FullTOC(test_data.FULL_TOC_KARMACODE)
        self.assertEqual(len(full_toc.sessions), 2)
        self.assertEqual(full_toc.sessions[0].number, 1)
        self.assertEqual(full_toc.sessions[0].firstTrack, 1)
        self.assertEqual(full_toc.sessions[0].lastTrack, 13)
        self.assertEqual(full_toc.sessions[0].leadout, cdrom.Address(213533))
        self.assertEqual(full_toc.sessions[0].discType,
                         cdrom.DISC_TYPE_CD)

        self.assertEqual(full_toc.sessions[1].number, 2)
        self.assertEqual(full_toc.sessions[1].firstTrack, 14)
        self.assertEqual(full_toc.sessions[1].lastTrack, 14)
        self.assertEqual(full_toc.sessions[1].leadout, cdrom.Address(255747))
        self.assertEqual(full_toc.sessions[1].discType,
                         cdrom.DISC_TYPE_CD_XA)

        self.checkTrack(full_toc, 1, 1, 0,
                        cdrom.Address(0), cdrom.Address(20010))
        self.checkTrack(full_toc, 2, 1, 0,
                        cdrom.Address(20010), cdrom.Address(35154))
        self.checkTrack(full_toc, 3, 1, 0,
                        cdrom.Address(35154), cdrom.Address(53388))
        self.checkTrack(full_toc, 4, 1, 0,
                        cdrom.Address(53388), cdrom.Address(69807))
        self.checkTrack(full_toc, 5, 1, 0,
                        cdrom.Address(69807), cdrom.Address(87262))
        self.checkTrack(full_toc, 6, 1, 0,
                        cdrom.Address(87262), cdrom.Address(94190))
        self.checkTrack(full_toc, 7, 1, 0,
                        cdrom.Address(94190), cdrom.Address(110773))
        self.checkTrack(full_toc, 8, 1, 0,
                        cdrom.Address(110773), cdrom.Address(129573))
        self.checkTrack(full_toc, 9, 1, 0,
                        cdrom.Address(129573), cdrom.Address(143202))
        self.checkTrack(full_toc, 10, 1, 0,
                        cdrom.Address(143202), cdrom.Address(161175))
        self.checkTrack(full_toc, 11, 1, 0,
                        cdrom.Address(161175), cdrom.Address(177133))
        self.checkTrack(full_toc, 12, 1, 0,
                        cdrom.Address(177133), cdrom.Address(195114))
        self.checkTrack(full_toc, 13, 1, 0,
                        cdrom.Address(195114), cdrom.Address(213533))
        self.checkTrack(full_toc, 14, 2, cdrom.CTRL_DATA_TRACK,
                        cdrom.Address(224933), cdrom.Address(255747))


class AddressTests(unittest.TestCase):
    def assertEqualMSF(self, addr, min, sec, frame):
        self.assertEqual(addr.min, min)
        self.assertEqual(addr.sec, sec)
        self.assertEqual(addr.frame, frame)

    def assertEqualLBA(self, addr, lba):
        self.assertEqual(addr.lba, lba)

    def testLBAtoMSF(self):
        self.assertEqualMSF(cdrom.Address(0), 0, 2, 0)
        self.assertEqualMSF(cdrom.Address(178072), 39, 36, 22)
        self.assertEqualMSF(cdrom.Address(224427), 49, 54, 27)

    def testMSFtoLBA(self):
        self.assertEqualLBA(cdrom.Address(26, 11, 25), 117700)
        self.assertEqualLBA(cdrom.Address(63, 03, 00), 283575)
        self.assertEqualLBA(cdrom.Address(0, 0, 0), -150)

    def testCmp(self):
        # Test comparison between two different Address objects
        # that both have the same value
        addr123 = cdrom.Address(1, 2, 3)
        addr123_2 = cdrom.Address(1, 2, 3)
        self.assertNotEqual(id(addr123), id(addr123_2))
        self.assertTrue(addr123 == addr123_2)
        self.assertFalse(addr123 != addr123_2)
        self.assertTrue(addr123 <= addr123_2)
        self.assertTrue(addr123 >= addr123_2)
        self.assertFalse(addr123 < addr123_2)
        self.assertFalse(addr123 > addr123_2)

        # Test against an Address with a smaller min value
        addr023 = cdrom.Address(0, 2, 3)
        self.assertFalse(addr123 == addr023)
        self.assertTrue(addr123 != addr023)
        self.assertFalse(addr123 <= addr023)
        self.assertTrue(addr123 >= addr023)
        self.assertFalse(addr123 < addr023)
        self.assertTrue(addr123 > addr023)

        # Test against an Address with a smaller sec value
        addr113 = cdrom.Address(1, 1, 3)
        self.assertFalse(addr123 == addr113)
        self.assertTrue(addr123 != addr113)
        self.assertFalse(addr123 <= addr113)
        self.assertTrue(addr123 >= addr113)
        self.assertFalse(addr123 < addr113)
        self.assertTrue(addr123 > addr113)

        # Test against an Address with a smaller frame value
        addr120 = cdrom.Address(1, 2, 0)
        self.assertFalse(addr123 == addr120)
        self.assertTrue(addr123 != addr120)
        self.assertFalse(addr123 <= addr120)
        self.assertTrue(addr123 >= addr120)
        self.assertFalse(addr123 < addr120)
        self.assertTrue(addr123 > addr120)

        # Test against an Address where min, sec, and frame are all different
        addr789 = cdrom.Address(7, 8, 9)
        self.assertFalse(addr123 == addr789)
        self.assertTrue(addr123 != addr789)
        self.assertTrue(addr123 <= addr789)
        self.assertFalse(addr123 >= addr789)
        self.assertTrue(addr123 < addr789)
        self.assertFalse(addr123 > addr789)


if __name__ == '__main__':
    unittest.main()
