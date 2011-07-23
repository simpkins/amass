#!/usr/bin/python -tt
#
# Copyright (c) 2011, Adam Simpkins
#
"""
Simple logger classes for writing log files.

These loggers are used for writing logs about the ripping process, etc.
This is independent of the normal program logging done by the standard logging
module.
"""

DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40


class NullLogger(object):
    def debug(self, *args):
        pass

    def info(self, *args):
        pass

    def warning(self, *args):
        pass

    def error(self, *args):
        pass


class FileLogger(object):
    def __init__(self, path, level):
        self.path = path
        self.log_file = open(path, 'a')
        self.level = level
        self.always_flush = True

    def debug(self, msg, *args):
        if self.level > DEBUG:
            return
        self.log(msg, *args)

    def info(self, msg, *args):
        if self.level > INFO:
            return
        self.log(msg, *args)

    def warning(self, msg, *args):
        if self.level > WARNING:
            return
        self.log(msg, *args)

    def error(self, msg, *args):
        if self.level > ERROR:
            return
        self.log(msg, *args)

    def log(self, msg, *args):
        if args:
            try:
                msg = msg % args
            except TypeError, ex:
                self.error('formatting error in log message: ' + str(ex))
                self.error('  args are: ' + repr(args))
        self.log_file.write(msg + '\n')
        if self.always_flush:
            self.log_file.flush()
