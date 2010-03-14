#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import os
import sys
import unittest

lib_dir = os.path.normpath(os.path.join(sys.path[0], '..', 'src'))
sys.path = [sys.path[0], lib_dir] + sys.path[1:]

from amass import proc


class RunCmdTests(unittest.TestCase):
    def testSuccess(self):
        (status, cmd_out, cmd_err) = proc.run_cmd(['/bin/true'])
        self.assertEqual(status, 0)
        self.assertEqual(cmd_out, '')
        self.assertEqual(cmd_err, '')

    def testFailure(self):
        try:
            proc.run_cmd(['/bin/false'])
            self.fail('run_cmd() failed to raise an exception')
        except proc.CmdFailedError, ex:
            self.assertEqual(ex.status, 1)

    def testSignal(self):
        try:
            proc.run_cmd(['/bin/sh', '-c', 'kill -9 $$'])
            self.fail('run_cmd() failed to raise an exception')
        except proc.CmdTerminatedError, ex:
            self.assertEqual(ex.signum, 9)

    def testOutput(self):
        cmd = ['/bin/sh', '-c', 'echo foo; echo bar >&2']
        (status, cmd_out, cmd_err) = proc.run_cmd(cmd)
        self.assertEqual(status, 0)
        self.assertEqual(cmd_out, 'foo\n')
        self.assertEqual(cmd_err, 'bar\n')

    def testOutputNoEOL(self):
        cmd = ['/bin/sh', '-c', 'echo -n foo; echo -n bar >&2']
        (status, cmd_out, cmd_err) = proc.run_cmd(cmd)
        self.assertEqual(status, 0)
        self.assertEqual(cmd_out, 'foo')
        self.assertEqual(cmd_err, 'bar')

    def testFailOutput(self):
        cmd = ['/bin/sh', '-c', 'echo -n foo; echo -n bar >&2; exit 17']
        (status, cmd_out, cmd_err) = proc.run_cmd_any(cmd)
        self.assertEqual(status, 17)
        self.assertEqual(cmd_out, 'foo')
        self.assertEqual(cmd_err, 'bar')


if __name__ == '__main__':
    unittest.main()
