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


def find_files_by_suffix(dir, suffix):
    files = []
    for entry in os.listdir(dir):
        if not entry.endswith(suffix):
            continue
        path = os.path.join(dir, entry)
        files.append(path)

    return files


def decode_path(path):
    """
    decode_path(str) --> unicode

    Attempt to decode a byte string path name to a unicode string.

    If the input is already a unicode string, it is returned as-is.
    If the input is not valid UTF-8 and cannot be decoded, the byte string will
    be returned as-is rather than throwing an error.
    """
    # We generally encode the path names as UTF-8 when writing them.
    # When reading path names, attempt to decode them from UTF-8 and
    # convert them back to a unicode string.  This way we can compare them
    # with the unicode strings that we use internally.
    if isinstance(path, str):
        try:
            return path.decode('utf-8')
        except UnicodeDecodeError:
            # Not a valid UTF-8 string.  Just keep using the plain
            # byte array
            return path
    else:
        # Already a unicode string
        return path


def safe_filename(name):
    """
    safe_filename(name) --> name

    Make a string safe for use as a file name.
    """
    # TODO: It would be nice to strip out non-printable characters, or replace
    # them with some dummy character.
    # TODO: Support making the name safe for Windows, too.
    return name.replace('/', '\\')
