#!/usr/bin/python -tt
#
# Copyright (c) 2010, Adam Simpkins
#
import errno
import os


def open_new(path):
    """
    Open a file, ensuring that it doesn't exist.
    Make its parent directory if necessary
    """
    # Optimistically try to open the file
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0666)
    except OSError, ex:
        if ex.errno == errno.ENOENT:
            # Create the parent directory and try again
            os.makedirs(os.path.dirname(path))
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0666)
        else:
            # All other errors are fatal
            raise

    return os.fdopen(fd, 'w')


def prepare_new(path):
    """
    Prepare to create a new file.

    Ensure that the parent directory exists.
    This is used before we call an external program to create a file.

    (We could also try to ensure that the file itself doesn't exist,
    but there doesn't seem to be a whole lot of benefit anyway.  Any check we
    do would be racy.)
    """
    try:
        os.makedirs(os.path.dirname(path))
    except OSError, ex:
        if ex.errno != errno.EEXIST:
            raise
