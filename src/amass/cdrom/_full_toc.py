#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import struct

from . import binary
from . import constants
from ._address import Address

__all__ = ['FullTOCEntry', 'FullTOC', 'read_full_toc']


class DupEntryError(Exception):
    def __init__(self, entry):
        Exception.__init__(self,
                           'duplicate TOC entry: session=%s, point=%s' %
                           (entry.session, entry.point))
        self.entry = entry


class FullTOCEntry(object):
    def __init__(self, tuple):
        (self.session, adr_ctrl, self.tno, self.point, self.min,
         self.sec, self.frame, self.zero, self.pmin, self.psec,
         self.pframe) = tuple

        (self.adr, self.ctrl) = binary.parse_adr_ctrl(adr_ctrl)


class SessionInfo(object):
    def __init__(self, number):
        self.number = number
        self.firstTrack = None
        self.lastTrack = None
        self.leadout = None
        self.discType = None


class TrackInfo(object):
    def __init__(self, number, session, ctrl, address):
        self.number = number
        self.sessionNumber = session
        self.address = address
        self.ctrl = ctrl

    def isDataTrack(self):
        return bool(self.ctrl & constants.CTRL_DATA_TRACK)


class FullTOC(object):
    def __init__(self, buf):
        parser = Parser(buf)
        parser.parse()

        self.sessions = parser.sessions
        self.tracks = parser.tracks
        self.rawEntries = parser.rawEntries

    def getSession(self, number):
        session = self.sessions[number - 1]
        assert session.number == number
        return session

    def getTrack(self, number):
        first_track_number = self.tracks[0].number
        track = self.tracks[number - first_track_number]
        assert track.number == number
        return track

    def toBuffer(self):
        data_len = 2 + (11 * len(self.rawEntries))

        format = '>HBB'
        args = [data_len, self.sessions[0].number, self.sessions[-1].number]

        # Note: The entries are required to be written out in a specific
        # order.  We currently rely on them being already in the proper
        # ordering.
        for entry in self.rawEntries:
            format += 'BBBBBBBBBBB'
            args += [entry.session,
                     binary.combine_adr_ctrl(entry.adr, entry.ctrl),
                     entry.tno, entry.point,
                     entry.min, entry.sec, entry.frame,
                     entry.zero,
                     entry.pmin, entry.psec, entry.pframe]

        return struct.pack(format, *args)


class Parser(object):
    def __init__(self, buf):
        self.buf = buf

        self.firstSession = None
        self.lastSession = None
        self.sessions = []
        self.tracks = []
        self.rawEntries = []
        self.tracksDict = {}
        self.sessionsDict = {}

    def parse(self):
        # Walk the buffer and parse each entry
        self.__parseBuffer()

        # Now examine the parsed track and session info,
        # re-arrange them into arrays, and make sure everything is valid.
        #
        # We could do this all in one pass, since the entries are required to
        # appear ordered by session, and within each session the entries must
        # appear 0xA0, 0xA1, 0xA2, then tracks, then 0xBX - 0xCX.  Using two
        # passes is just easier at the moment.
        #
        # TODO: If we used a single pass, we could also validate that the
        # entries are in fact ordered correctly.  It's unclear if it would be
        # better to perform strict validation of the ordering, or to be
        # lenient, as we are now.
        self.__validateSessions()
        self.__validateTracks()

    def __parseBuffer(self):
        header = struct.unpack_from('>HBB', self.buf, 0)
        (data_len, self.firstSession, self.lastSession) = header

        offset = 4
        end_offset = data_len + 2
        entry_len = 11
        entries = []
        while offset + entry_len <= end_offset:
            entry_tuple = struct.unpack_from('>BBBBBBBBBBB', self.buf, offset)
            #print ' '.join('%02X' % (b,) for b in entry_tuple)
            entry = FullTOCEntry(entry_tuple)
            self.__parseEntry(entry)

            offset += entry_len

        # Make sure the data length ended at an entry boundary
        if offset != end_offset:
            raise Exception('full TOC data length does not end on an entry '
                            'boundary: length=%d, %d bytes leftover' %
                            (data_len, end_offset - offset))

    def __parseEntry(self, entry):
        self.rawEntries.append(entry)
        if entry.adr == 1:
            self.__parseMode1Entry(entry)
        elif entry.adr == 5:
            self.__parseMode5Entry(entry)
        else:
            self.__unknownEntry(entry)

    def __parseMode1Entry(self, entry):
        if 1 <= entry.point and entry.point <= 99:
            self.__parseTrackEntry(entry)
        elif entry.point == 0xa0:
            self.__sessionFirstTrack(entry)
        elif entry.point == 0xa1:
            self.__sessionLastTrack(entry)
        elif entry.point == 0xa2:
            self.__sessionLeadout(entry)
        else:
            self.__unknownEntry(entry)

    def __parseTrackEntry(self, entry):
        addr = Address(entry.pmin, entry.psec, entry.pframe)
        track_info = TrackInfo(entry.point, entry.session, entry.ctrl, addr)
        if self.tracksDict.has_key(entry.point):
            raise DupEntryError(entry)
        self.tracksDict[entry.point] = track_info

    def __getSession(self, number):
        try:
            session = self.sessionsDict[number]
        except KeyError:
            session = SessionInfo(number)
            self.sessionsDict[number] = session

        return session

    def __sessionFirstTrack(self, entry):
        # Session's first track # in entry.pmin
        session_info = self.__getSession(entry.session)
        if session_info.firstTrack is not None:
            raise DupEntryError(entry)
        session_info.firstTrack = entry.pmin

        # disc type in entry.psec
        if session_info.discType is not None:
            raise DupEntryError(entry)
        session_info.discType = entry.psec

    def __sessionLastTrack(self, entry):
        # Session's last track # in entry.pmin
        session_info = self.__getSession(entry.session)
        if session_info.lastTrack is not None:
            raise DupEntryError(entry)
        session_info.lastTrack = entry.pmin

    def __sessionLeadout(self, entry):
        # Lead-out address
        session_info = self.__getSession(entry.session)
        if session_info.leadout is not None:
            raise DupEntryError(entry)

        session_info.leadout = Address(entry.pmin, entry.psec, entry.pframe)

    def __parseMode5Entry(self, entry):
        # Mode 5 is only used for recordable media.
        # XXX: At the moment, we don't store any of this parsed data.
        if 0x01 <= entry.point and entry.point <= 0x40:
            # - pmin, psec, pframe: start of interval to skip
            # - min, sec, frame: end of interval to skip
            pass
        elif entry.point == 0xb0:
            # - min, sec, frame contains start of next possible program in
            #   the Recordable Area of the disc.
            # - zero contains # of pointers in Mode 5
            # - pmin, psec, pframe contains max start time of outer-most
            #   lead-out area in the Recordable Area of the disc
            pass
        elif entry.point == 0xb1:
            # pmin: number of skip interval Pointers (N <= 40)
            # psec: number of skip interval Pointers (N <= 21)
            pass
        elif 0xb2 <= entry.point and entry.point <= 0xb4:
            # min, sec, frame, zero, pmin, psec, pframe:
            #   all contain skip numbers
            pass
        elif entry.point == 0xc0:
            # min = optimum recording power
            # pmin, psec, pframe = start time of the first Lead-in Area
            #   of the disc
            pass
        elif entry.point == 0xc1:
            # min, sec, frame, zero, pmin, psec, pframe:
            #   copy of information from A1 point in ATIP
            pass
        else:
            self.__unknownEntry(entry)

    def __unknownEntry(self, entry):
        """
        This method is called when we encounter an unexpected
        entry in the table of contents.
        """
        # For now, we just ignore unrecognized entries.
        pass

    def __validateSessions(self):
        # Get the sessions as an array, sorted in increasing order
        self.sessions = sorted(self.sessionsDict.itervalues(),
                               key=lambda s: s.number)
        # Make sure the sessions start at 1, and increase consecutively
        expected_number = 1
        for session in self.sessions:
            if session.number != expected_number:
                raise Exception('TOC has non-consecutive sessions: '
                                'expected to find session %d next, found %d' %
                                (expected_number, session.number))
            expected_number += 1

            # Make sure each session has all the required fields
            if session.firstTrack is None:
                raise Exception('missing first track number for session %d' %
                                (session.number,))
            if session.lastTrack is None:
                raise Exception('missing last track number for session %d' %
                                (session.number,))
            if session.leadout is None:
                raise Exception('missing leadout address for session %d' %
                                (session.number,))
            if session.discType is None:
                raise Exception('missing disc type for session %d' %
                                (session.number,))

        # Make sure self.firstSession and self.lastSession are accurate
        if self.firstSession != self.sessions[0].number:
            raise Exception('invalid first session number in TOC: '
                            'value is %d, actual first session is %d' %
                            (self.firstSession, self.sessions[0].number))

        if self.lastSession != self.sessions[-1].number:
            raise Exception('invalid last session number in TOC: '
                            'value is %d, actual last session is %d' %
                            (self.lastSession, self.sessions[-1].number))

    def __validateTracks(self):
        # Get the tracks as an array, sorted in increasing number
        self.tracks = sorted(self.tracksDict.itervalues(),
                             key=lambda t: t.number)

        first_track_number = self.sessions[0].firstTrack
        expected_number = first_track_number
        for track in self.tracks:
            # Make sure the tracks increase consecutively
            # From section 3.1 of the Mt. Fuji spec:
            #  The Tracks of a CD media are numbered consecutively with values
            #  between 1 and 99.  However, the first information Track may have
            #  a number greater than 1.
            if track.number != expected_number:
                raise Exception('TOC has non-consecutive tracks: '
                                'expected to find tracks %d next, found %d' %
                                (expected_number, track.number))
            expected_number += 1

            # Set the track.session attribute
            session = self.sessions[track.sessionNumber - 1]
            assert session.number == track.sessionNumber
            track.session = session

            # Compute the end address for each track
            if track.number == session.lastTrack:
                track.endAddress = session.leadout
            else:
                next_track_idx = (track.number + 1) - first_track_number
                next_track = self.tracks[next_track_idx]
                track.endAddress = next_track.address


def read_full_toc(device):
    buf = binary.read_full_toc(device)
    return FullTOC(buf)
