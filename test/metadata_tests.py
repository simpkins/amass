#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import os
import sys
import unittest

lib_dir = os.path.normpath(os.path.join(sys.path[0], '..', 'src'))
sys.path = [sys.path[0], lib_dir] + sys.path[1:]

from amass import metadata
from amass.metadata.field_types import *


class TitleScoreTests(unittest.TestCase):
    def testScoreMissingCaps(self):
        value = 'This is a Test'
        self.assertTrue(TitleField.computeScore(value) < SCORE_GOOD)

    def testScoreCapitalized(self):
        value = 'This Is A Test'
        self.assertTrue(TitleField.computeScore(value) >= SCORE_GOOD)


if __name__ == '__main__':
    unittest.main()
