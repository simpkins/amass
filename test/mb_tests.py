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
from amass import mb
import test_data


class CddbTests(unittest.TestCase):
    def testIdGlassworks(self):
        full_toc = cdrom.FullTOC(test_data.FULL_TOC_GLASSWORKS)
        mb_id = mb.get_mb_id(full_toc)
        self.assertEqual(mb_id, '_sVrFDJnz7X5AIOYy.XRbvAkQbU-')

    def testIdKarmacode(self):
        full_toc = cdrom.FullTOC(test_data.FULL_TOC_KARMACODE)
        mb_id = mb.get_mb_id(full_toc)
        self.assertEqual(mb_id, 'ZAYb2mGXra1AThXV8qSzGCyiu.4-')

    def testIdDuskAndSummer(self):
        full_toc = cdrom.FullTOC(test_data.FULL_TOC_DUSK_AND_SUMMER)
        mb_id = mb.get_mb_id(full_toc)
        self.assertEqual(mb_id, '7M1ELM7spLD.scP31hAy15Di0g8-')


if __name__ == '__main__':
    unittest.main()
