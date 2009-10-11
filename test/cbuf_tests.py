#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import os
import sys
import unittest

lib_dir = os.path.normpath(os.path.join(sys.path[0], '..', 'src'))
sys.path = [sys.path[0], lib_dir] + sys.path[1:]

from amass import cbuf


class CbufTests(unittest.TestCase):
    def __getCbuf32(self):
        cb = cbuf.CBuffer('\x00\x01\x02\x03\x04\x05\x06\x07'
                          '\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
                          '\x10\x11\x12\x13\x14\x15\x16\x17'
                          '\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f')
        return cb

    def testLen(self):
        cb = self.__getCbuf32()
        self.assertEqual(len(cb), 32)

        cb = cbuf.CBuffer(19)
        self.assertEqual(len(cb), 19)

    def testGetEndianness(self):
        cb = self.__getCbuf32()

        self.assertEqual(cb.getU16BE(0), 0x0001)
        self.assertEqual(cb.getU16LE(0), 0x0100)

        self.assertEqual(cb.getU16BE(0x13), 0x1314)
        self.assertEqual(cb.getU16LE(0x13), 0x1413)

        self.assertEqual(cb.getU32BE(0x16), 0x16171819)
        self.assertEqual(cb.getU32LE(0x16), 0x19181716)

        self.assertEqual(cb.getU64BE(0x0e), 0x0e0f101112131415)
        self.assertEqual(cb.getU64LE(0x0e), 0x1514131211100f0e)

        self.assertRaises(IndexError, cb.getU64LE, 0x1c)

    def testGetItem(self):
        cb = self.__getCbuf32()
        self.assertEqual(cb[0x1b], '\x1b')
        self.assertEqual(cb[-1], '\x1f')
        self.assertEqual(cb[-0x1f], '\x01')

        self.assertRaises(IndexError, eval, 'cb[32]', globals(), locals())
        self.assertRaises(IndexError, eval, 'cb[100]', globals(), locals())
        self.assertRaises(IndexError, eval, 'cb[-40]', globals(), locals())

    def testGetSlice(self):
        cb = self.__getCbuf32()
        self.assertEqual(cb[0x1b:0x1e], '\x1b\x1c\x1d')
        self.assertEqual(cb[0x1b:], '\x1b\x1c\x1d\x1e\x1f')
        self.assertEqual(cb[:4], '\x00\x01\x02\x03')
        self.assertEqual(cb[:], ''.join([chr(x) for x in range(32)]))
        self.assertEqual(cb[33:40], '')

        self.assertEqual(cb[-5:], '\x1b\x1c\x1d\x1e\x1f')
        self.assertEqual(cb[-5:-1], '\x1b\x1c\x1d\x1e')

        s = 'foobar'
        cb = cbuf.CBuffer(s)
        self.assertEqual(s, cb[:])

    def testSetItem(self):
        cb = self.__getCbuf32()
        cb[6] = 0x19
        cb[7] = 0xff
        cb[8] = 0x93
        cb[9] = 0x03
        self.assertEqual(cb.getU32BE(6), 0x19ff9303)

        cb[-3] = 0
        self.assertEqual(cb.getU32BE(-4), 0x1c001e1f)

        try:
            cb[32] = 5
            self.fail('expected IndexError')
        except IndexError:
            pass

        try:
            cb[-100] = 5
            self.fail('expected IndexError')
        except IndexError:
            pass

    def testSetSlice(self):
        cb = self.__getCbuf32()
        cb[6:10] = [0x19, 0xff, 0x93, 0x03]
        self.assertEqual(cb.getU32BE(6), 0x19ff9303)

        cb[-3:] = '\x12\x34\x56'
        self.assertEqual(cb.getU32BE(-4), 0x1c123456)

        cb[:2] = '\x99\xaa'
        self.assertEqual(cb.getU32BE(0), 0x99aa0203)

        try:
            cb[32] = 5
            self.fail('expected IndexError')
        except IndexError:
            pass

        try:
            cb[-100] = 5
            self.fail('expected IndexError')
        except IndexError:
            pass


if __name__ == '__main__':
    unittest.main()
