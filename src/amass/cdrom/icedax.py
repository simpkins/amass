#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import os
import re
import shutil
import subprocess
import tempfile


class TempDir(object):
    def __init__(self, suffix='', prefix='tmp', dir=None):
        self.path = None # This way self.path will be set even if mkdtemp fails
        self.path = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=dir)

    def cleanup(self):
        if self.path is None:
            return

        shutil.rmtree(self.path, ignore_errors=True)

    def __del__(self):
        self.cleanup()


class TrackInfo(object):
    def __init__(self, info, name):
        self.info = info
        self.name = name

    def getNumber(self):
        return self.getIntField('Tracknumber')

    def getStartSector(self):
        return self.getIntField('Trackstart')

    def getNumSectors(self):
        # icedax writes it out as <sectors>, <samples>
        # <samples> should always be 0, though.
        m = self.matchField('Tracklength', '^(\d+), (\d+)$')
        sectors = int(m.group(1))
        samples = int(m.group(2))
        if samples != 0:
            # If samples is non-zero, the track ends in the middle of a sector.
            # This can't happen.  (I'm not sure why icedax prints it out
            # separately like this.  Internally it converts a sector number to
            # a number of samples, then back down to #sectors,#samples.)
            raise Exception('icedax reports a non-integral number of sectors '
                            'in track')
        return sectors

    def getTitle(self):
        return self.getQuotedField('Tracktitle')

    def getPerformer(self):
        return self.getQuotedField('Performer')

    def getAlbum(self):
        return self.getQuotedField('Albumtitle')

    def getAlbumPerformer(self):
        return self.getQuotedField('Albumperformer')

    def getMCN(self):
        return self.getPlainField('MCN')

    def getISRC(self):
        v = self.getPlainField('ISRC')
        # icedax pads this field with spaces.  Strip them off.
        return v.strip()

    def getCddbId(self):
        m = self.matchField('CDDB_DISCID', '^0x([A-Fa-f0-9]+)$')
        return int(m.group(1), 16)

    def getIndices(self):
        v = self.getPlainField('Index')
        try:
            indices = [int(i) for i in v.split()]
        except ValueError:
            raise Exception('unexpected value for Index: %r' % (v,))

        return indices

    def getNextTrackPreGap(self):
        # Will return -1 if there is no pre-gap before the next track
        return self.getIntField('Index0')

    # Helper methods
    def getPlainField(self, name):
        # May raise KeyError
        return self.info[name]

    def getIntField(self, name):
        # We don't use matchField(name, '^(\d+)$' here, because
        # icedax puts extraneous space around some integer fields
        # (such as Index0)
        # May raise KeyError
        v = self.info[name]
        return int(v)

    def getQuotedField(self, name):
        m = self.matchField(name, "^'(.*)'$")
        return m.group(1)

    def matchField(self, name, regex):
        # May raise KeyError
        value = self.info[name]

        # Verify that the value matches the the regular expression
        m = re.search(regex, value)
        if not m:
            raise Exception('unexpected value for %r in icedax info: %r' %
                            (name, value))
        return m


def get_info(device):
    tmpdir = TempDir(prefix='amass-icedax-')

    write_info_files(device, tmpdir.path)
    tracks = parse_info_dir(tmpdir.path)

    tmpdir.cleanup()

    return tracks


def write_info_files(device, dir):
    """
    Write audio_XX.inf files for the specified device into the
    specified directory.
    """
    cmd = ['icedax', 'dev=%s' % (device,), '-J', '-v', 'all']
    p = subprocess.Popen(cmd, cwd=dir,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    status = p.wait()
    if status != 0:
        raise Exception('icedax returned %s:\n%s' % (err,))


def parse_info_dir(path):
    tracks = []

    # Walk the entries in sorted order, so we see the tracks in order
    expected_track_num = 1
    for entry in sorted(os.listdir(path)):
        # Only parse audio_XX.inf files
        if not (entry.startswith('audio_') and entry.endswith('.inf')):
            continue

        # Parse the file
        full_path = os.path.join(path, entry)
        info = parse_info_file(full_path, name=entry)

        # Make sure the track number is what we expect
        if info.getNumber() != expected_track_num:
            raise Exception('expected info for track number %d, found %d' %
                            (expected_track_num, info.getTrackNumber()))
        expected_track_num += 1

        tracks.append(info)

    return tracks


def parse_info_file(path, name=None):
    if name is None:
        name = path

    f = open(path, 'r')
    data = f.read()
    f.close()

    return parse_info_string(data, name)


def parse_info_string(data, name):
    info = {}
    for line in data.splitlines():
        if not line:
            # ignore blank lines
            continue

        if line.startswith('#'):
            # ignore comments
            continue

        try:
            key, value = line.split('=', 1)
        except ValueError:
            raise Exception('unexpected line in icedax info file %r: %r' %
                            (path, line))

        # Ignore tabs after the '='
        value = value.lstrip('\t')

        if info.has_key(key):
            raise Exception('duplicate key %r in icedax info file %r' %
                            (key, path))
        info[key] = value

    return TrackInfo(info, name)
