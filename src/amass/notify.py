#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
"""
Functions for notifying the user of various types of messages.
"""


def warn(msg):
    print >> sys.stderr, 'warning: %s' % (msg,)
