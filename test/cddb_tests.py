#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import os
import sys
import unittest

lib_dir = os.path.normpath(os.path.join(sys.path[0], '..', 'src'))
sys.path = [sys.path[0], lib_dir] + sys.path[1:]

from amass import cddb
from amass import cdrom
import test_data


class CddbTests(unittest.TestCase):
    def testIdGlassworks(self):
        full_toc = cdrom.FullTOC(test_data.FULL_TOC_GLASSWORKS)
        cddb_id = cddb.get_cddb_id(full_toc)
        self.assertEqual(cddb_id, 0xa40ec50b)

    def testIdKarmacode(self):
        full_toc = cdrom.FullTOC(test_data.FULL_TOC_KARMACODE)
        cddb_id = cddb.get_cddb_id(full_toc)
        self.assertEqual(cddb_id, 0xab0d510e)

    def testIdDuskAndSummer(self):
        full_toc = cdrom.FullTOC(test_data.FULL_TOC_DUSK_AND_SUMMER)
        cddb_id = cddb.get_cddb_id(full_toc)
        self.assertEqual(cddb_id, 0xa809870a)


if __name__ == '__main__':
    unittest.main()
