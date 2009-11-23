#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import io
import re

from . import err


MULTI_ARTIST_NAME = 'Various'


class Data(object):
    def __init__(self):
        self.fields = {}
        self.trackOffsets = []
        self.discLength = None
        self.revision = None
        self.submittedVia = None

    def getArtist(self):
        return self.getArtistAndTitle()[0]

    def getTitle(self):
        return self.getArtistAndTitle()[1]

    def getArtistAndTitle(self):
        return self.parseArtistAndTitle(self.fields['DTITLE'])

    def parseArtistAndTitle(self, field):
        s = field.split(' / ', 1)
        if len(s) == 1:
            return (s[0], s[0])
        else:
            return (s[0], s[1])

    def isMultiArtist(self):
        return self.getArtist() == MULTI_ARTIST_NAME

    def getNumTracks(self):
        return len(self.trackOffsets)

    def getTrackOffset(self, track_num):
        """
        getTrackOffset(track_num) --> offset
        Returns the offset of the specified track, in frames.  Tracks are
        indexed starting at 1.

        Raises an IndexError if the track number is invalid.
        """
        if track_num < 0 or track_num > len(self.trackOffsets):
            raise IndexError('invalid track number: %d' % (track_num,))
        return self.trackOffsets[track_num - 1]

    def getDiscId(self):
        return self.fields.get('DISCID', None)

    def getYear(self):
        return self.fields.get('DYEAR', None)

    def getGenre(self):
        return self.fields.get('DGENRE', None)

    def getTrackArtist(self, track_num):
        if track_num < 1 or track_num > len(self.trackOffsets):
            raise IndexError('invalid track number: %d' % (track_num,))
        if self.isMultiArtist():
            title_str = self.getParameter('TTITLE%d' % (track_num - 1))
            return self.parseArtistAndTitle(title_str)[0]
        else:
            return self.getArtist()

    def getTrackTitle(self, track_num):
        if track_num < 1 or track_num > len(self.trackOffsets):
            raise IndexError('invalid track number: %d' % (track_num,))
        title_str = self.getParameter('TTITLE%d' % (track_num - 1))
        if self.isMultiArtist():
            return self.parseArtistAndTitle(title_str)[1]
        else:
            return title_str

    def validate(self):
        # Check for the required parameters
        required_params = \
        [
            'DISCID',
            'DTITLE',
            'DYEAR',
            'DGENRE',
        ]
        missing_params = []
        for param in required_params:
            if not self.fields.has_key(param):
                missing_params.append(param)
        if len(missing_params) != 0:
            missing_str = ', '.join(missing_params)
            raise err.DataError('missing required parameters: ' + missing_str)

        # Make sure that the number of offsets matches
        # the number of track titles
        num_offsets = len(self.trackOffsets)
        num_tracks = 0
        while True:
            track_param = 'TTITLE%d' % num_tracks
            if self.fields.has_key(track_param):
                num_tracks += 1
            else:
                break

        if num_tracks != num_offsets:
            if not self.fields.has_key(track_param):
                msg = ('found title information for %d tracks, ' \
                        'but offset information for %d tracks') % \
                        (num_tracks, num_offsets)
                raise err.DataError(msg)


class Parser(object):
    """
    Class for parsing a CDDB entry.

    Data format documented at:
    http://ftp.freedb.org/pub/freedb/latest/DBFORMAT
    """
    def __init__(self, buf):
        if isinstance(buf, bytes):
            buf = buf.decode('UTF-8')

        # Split the buffer into lines
        self.lines = buf.split('\n')
        self.lineNumber = 0

        # Compile regular expressions that we will use
        self.reOffsetStart = re.compile(r'#\s*Track frame offsets:')
        self.reOffset = re.compile(r'#\s*(\d+)')
        self.reDiscLength = re.compile(r'#\s*Disc length:\s*(\d+)\s*seconds')
        self.reRevision = re.compile(r'#\s*Revision:\s*(\d+)')
        self.reSubmittedVia = re.compile(r'#\s*Submitted via:\s*(.+)')

        # The Data object to store parsed data into
        self.data = Data()

    def parse(self):
        # The first line should start with '# xmcd'
        # to identify this as a CDDB file
        line = self.nextLine()
        if not line.startswith('# xmcd'):
            self.parseError('missing "# xmcd" prefix')

        while self.hasMoreLines():
            line = self.nextLine()

            if not line:
                # The DBFORMAT document says blank lines aren't allowed.
                # We just ignore them, though.
                continue

            if line[0] == '#':
                self.parseComment(line)
            else:
                self.parseKeyword(line)

        self.data.validate()
        return self.data

    def parseComment(self, line):
        # The DBFORMAT document indicates that the contents must appear in the
        # following order:
        #
        # - Comments:
        #   - xmcd comment on first line
        #   - Track frame offsets list next
        #   - Disc length
        #   - Revision
        #   - Submitted via
        # - Disc data
        #
        # We don't enforce this strict ordering, though.  We also currently
        # allow the data in the comments to appear multiple times.  (In this
        # case, the last appearance wins.)
        match = self.reOffsetStart.match(line)
        if match:
            self.parseTrackOffsets()
            return

        match = self.reDiscLength.match(line)
        if match:
            self.data.discLength = int(match.group(1))
            return

        match = self.reRevision.match(line)
        if match:
            self.data.revision = int(match.group(1))
            return

        match = self.reSubmittedVia.match(line)
        if match:
            self.data.submittedVia = match.group(1)
            return

        # Ignore other comments
        return

    def parseTrackOffsets(self):
        while self.hasMoreLines():
            line = self.nextLine()

            match = self.reOffset.match(line)
            if not match:
                self.unreadLine()
                return

            offset = int(match.group(1))
            self.data.trackOffsets.append(offset)

    def parseKeyword(self, line):
        # Should be <KEYWORD>=<value>
        try:
            (key, value) = line.split('=', 1)
        except ValueError:
            self.parseError('expected KEY=VALUE')

        # Unescape the value
        value = value.replace(r'\t', '\t')
        value = value.replace(r'\n', '\n')
        value = value.replace(r'\\', '\\')

        if self.data.fields.has_key(key):
            if key == 'DISCID' or key == 'PLAYORDER':
                # These fields contain numeric data, separated by commas.
                # They are different from other fields in that data on
                # subsequent lines is treated as a list of additional numbers
                # (with an implied comma).
                #
                # e.g.:
                #  PLAYORDER=1,2,3,4
                #  PLAYORDER=5,6,7,8
                #
                # should be read as "1,2,3,4,5,6,7,8", not "1,2,3,45,6,7,8"
                self.data.fields[key] = self.data.fields[key] + ',' + value
            else:
                self.data.fields[key] = self.data.fields[key] + value
        else:
            self.data.fields[key] = value

    def hasMoreLines(self):
        return self.lineNumber < len(self.lines)

    def nextLine(self):
        line = self.lines[self.lineNumber]
        self.lineNumber += 1

        # In case '\r\n' was used as line terminators,
        # strip off any trailing '\r'
        if line and line[-1] == '\r':
            line = line[:-1]

        return line

    def unreadLine(self):
        self.lineNumber -= 1

    def parseError(self, msg):
        raise err.ParseError(self.lineNumber, msg)


def parse(buf):
    return Parser(buf).parse()
