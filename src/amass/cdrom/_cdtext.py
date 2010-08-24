#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import os
import logging
import shutil
import struct
import subprocess
import sys
import tempfile

from ._err import *
from . import binary

# Tracking down freely available information about CD-TEXT is a bit of a pain.
# The definitive standard is the Red Book (there is a CD-TEXT addendum), which
# is not freely available.  (A license from Philips is about $5000.  IEC 60908
# is only $260, but as far as I can tell, may not include CD-TEXT information.)
#
# The SCSI MMC-2 and MMC-3 drafts both contain an appendix section with a brief
# description of the CD-TEXT.  It doesn't cover all of the details, though, and
# is pretty poorly written.  Unfortunately, the INCITS T10 committee started
# restricting access to the SCSI MMC specifications in January 2009.
#
# Freely available sources of information:
# - Appendix G of SFF 8090 (ftp://ftp.seagate.com/sff/INF-8090.PDF) contains
#   some information about the CD-TEXT format.  (This is very similar to the
#   information in the SCSI MMC-2 and -3 documents, but it has fixed a few
#   documentation bugs and some of the horrible grammar.)
#
# - US Patent #6519676 documents the CD-TEXT format quite well.  This is the
#   best source of information I have found so far.  (This patent seems to
#   cover parsing CD-TEXT information with a computer.  IANAL, but this seems
#   extremely broad, and far from non-obvious.  It also seems weird that this
#   patent was filed in 1999, despite the fact that CD-TEXT had been around for
#   several years by then.  The Philips website indicates that the Red Book
#   addendum on CD-TEXT was published in September of 1996.)
#
# - The icedax source code has routines to parse CD-TEXT.  "icedax -J"
#   will parse CD-TEXT information and write it in the resulting .inf files.
#   However, it doesn't parse all of the CD-TEXT fields.
#
# I've run across some documents on the web which indicates that CD-TEXT uses
# ITTS, which is specified in IEC 61886 (also not free).

# Character codes (Text byte 1 of pack ID 0x8f, element 0):
# (Information from US Patent #6519676)
CHARACTER_CODES = \
{
    0x00 : 'ISO 8859-1',
    0x01 : 'ASCII', # ISO 646
    # 0x02 - 0x7F: reserved
    0x80 : 'MS-JIS', # (simpkins: Shift-JIS ?)
    0x81 : 'Korean', # (simpkins: ?)
    0x82 : 'Mandarin', # (simpkins: ?)
    # 0x83 - 0xFF: reserved
}

# Language codes (text6 - text12 of pack ID 0x8f, element 2)
# (Information from US Patent #6519676)
LANGUAGE_NAMES = \
[
    # European
    'Unknown/Not Applicable',   # 0x00
    'Albanian',                 # 0x01
    'Breton',                   # 0x02
    'Catalan',                  # 0x03
    'Croatian',                 # 0x04
    'Welsh',                    # 0x05
    'Czech',                    # 0x06
    'Danish',                   # 0x07
    'German',                   # 0x08
    'English',                  # 0x09
    'Spanish',                  # 0x0A
    'Esperanto',                # 0x0B
    'Estonian',                 # 0x0C
    'Basque',                   # 0x0D
    'Faroese',                  # 0x0E
    'French',                   # 0x0F
    'Frisian',                  # 0x10
    'Irish',                    # 0x11
    'Gaelic',                   # 0x12
    'Galician',                 # 0x13
    'Icelandic',                # 0x14
    'Italian',                  # 0x15
    'Lappish',                  # 0x16
    'Latin',                    # 0x17
    'Latvian',                  # 0x18
    'Luxembourgian',            # 0x19
    'Lithuanian',               # 0x1A
    'Hungarian',                # 0x1B
    'Maltese',                  # 0x1C
    'Dutch',                    # 0x1D
    'Norwegian',                # 0x1E
    'Occitan',                  # 0x1F
    'Polish',                   # 0x20
    'Portuguese',               # 0x21
    'Romanian',                 # 0x22
    'Romansh',                  # 0x23
    'Serbian',                  # 0x24
    'Slovak',                   # 0x25
    'Slovene',                  # 0x26
    'Finnish',                  # 0x27
    'Swedish',                  # 0x28
    'Turkish',                  # 0x29
    'Flemish',                  # 0x2A
    'Walloon',                  # 0x2B
    None,                       # 0x2C
    None,                       # 0x2D
    None,                       # 0x2E
    None,                       # 0x2F
    None,                       # 0x30 Reserved for national assignment
    None,                       # 0x31 Reserved for national assignment
    None,                       # 0x32 Reserved for national assignment
    None,                       # 0x33 Reserved for national assignment
    None,                       # 0x34 Reserved for national assignment
    None,                       # 0x35 Reserved for national assignment
    None,                       # 0x36 Reserved for national assignment
    None,                       # 0x37 Reserved for national assignment
    None,                       # 0x38 Reserved for national assignment
    None,                       # 0x39 Reserved for national assignment
    None,                       # 0x3A Reserved for national assignment
    None,                       # 0x3B Reserved for national assignment
    None,                       # 0x3C Reserved for national assignment
    None,                       # 0x3D Reserved for national assignment
    None,                       # 0x3E Reserved for national assignment
    None,                       # 0x3F Reserved for national assignment
    # Non-European
    None,                       # 0x40
    None,                       # 0x41
    None,                       # 0x42
    None,                       # 0x43
    None,                       # 0x44
    'Zulu',                     # 0x45
    'Vietnamese',               # 0x46
    'Uzbek',                    # 0x47
    'Urdu',                     # 0x48
    'Ukrainian',                # 0x49
    'Thai',                     # 0x4A
    'Telugu',                   # 0x4B
    'Tatar',                    # 0x4C
    'Tamil',                    # 0x4D
    'Tadzhik',                  # 0x4E
    'Swahili',                  # 0x4F
    'Sranan Tor',               # 0x50
    'Somali',                   # 0x51
    'Sinhalese',                # 0x52
    'Shona',                    # 0x53
    'Serbo-Croation',           # 0x54
    'Ruthenian',                # 0x55
    'Russian',                  # 0x56
    'Quechua',                  # 0x57
    'Pushtu',                   # 0x58
    'Punjabi',                  # 0x59
    'Persian',                  # 0x5A
    'Papamiento',               # 0x5B
    'Oriya',                    # 0x5C
    'Nepali',                   # 0x5D
    'Ndebele',                  # 0x5E
    'Marathi',                  # 0x5F
    'Moldavian',                # 0x60
    'Malaysian',                # 0x61
    'Malagasay',                # 0x62
    'Macedonian',               # 0x63
    'Laotian',                  # 0x64
    'Korean',                   # 0x65
    'Khmer',                    # 0x66
    'Kazakh',                   # 0x67
    'Kannada',                  # 0x68
    'Japanese',                 # 0x69
    'Indonesian',               # 0x6A
    'Hindi',                    # 0x6B
    'Hebrew',                   # 0x6C
    'Hausa',                    # 0x6D
    'Gurani',                   # 0x6E
    'Gujurati',                 # 0x6F
    'Greek',                    # 0x70
    'Georgian',                 # 0x71
    'Fulani',                   # 0x72
    'Dariic',                   # 0x73
    'Churash',                  # 0x74
    'Chinese',                  # 0x75
    'Burmese',                  # 0x76
    'Bulgarian',                # 0x77
    'Bengali',                  # 0x78
    'Belorussian',              # 0x79
    'Bambora',                  # 0x7A
    'Azerbijani',               # 0x7B
    'Assamese',                 # 0x7C
    'Armenian',                 # 0x7D
    'Arabic',                   # 0x7E
    'Amharic',                  # 0x7F
]

# Symbolic constants for language codes
# For now I've only defined the ones I use.
LANGUAGE_UNKNOWN = 0x00
LANGUAGE_ENGLISH = 0x09

# Pack ID values
ID_TITLE = 0x80
ID_PERFORMER = 0x81
ID_SONGWRITER = 0x82
ID_COMPOSER = 0x83
ID_ARRANGER = 0x84
ID_MESSAGE = 0x85
ID_DISC_ID = 0x86
ID_GENRE = 0x87 # US Patent #6519676 lists this as "search keyword"
ID_TOC = 0x88
ID_TOC2 = 0x89
# 0x8a - 0x8c are reserved
# 0x8d is "reserved for content provider only"
ID_UPC_ISRC = 0x8e # Album UPC/EAN code for track 0, ISRC code for tracks
ID_SIZE_INFO = 0x8f

# Module-global logger
log = logging.getLogger('amass.cdrom.cdtext')


class CdText(object):
    def __init__(self, blocks):
        self.blocks = list(blocks)

    def getBlock(self, language):
        for block in self.blocks:
            if block.language == language:
                return block

        raise KeyError(language)


class Pack(object):
    def __init__(self, data, seq_num):
        self.seqNum = seq_num

        # Make sure the length is correct
        if len(data) != 18:
            raise CdTextError('invalid pack length %d for pack %d; '
                              'must be 18' % (len(data), seq_num))

        # Verify the pack checksum
        self.__verifyCRC(data)

        # Parse the fields
        (self.id, self.trackNumber, parsed_seq, block_info, self.value,
         self.checksum) = struct.unpack('>BBBB12sH', data)

        # Make sure the parsed sequence number matches what was expected
        if parsed_seq != seq_num:
            raise CdTextError('unexpected sequence number %d in CD-TEXT pack; '
                              'expecting %d' % (parsed_seq, seq_num))

        # Parse the block/char position byte
        self.dbcc = (block_info >> 7) & 0b1
        self.blockNumber = (block_info >> 4) & 0b111
        self.charPosition = block_info & 0b1111

    def __verifyCRC(self, data):
        # Invert the bits in the checksum
        verify_data = (data[:16] + chr(ord(data[16]) ^ 0xff) +
                       chr(ord(data[17]) ^ 0xff))
        # Compute the CRC over the modified data,
        # and make sure it is 0.
        crc = self.__computeCRC(verify_data)
        if crc != 0:
            raise CdTextError('CRC error in CD-TEXT pack %d' % (self.seqNum,))

    def __computeCRC(self, data):
        # CD-TEXT uses a 16-bit CCITT CRC
        crc = 0
        for byte in data:
            crc = crc ^ (ord(byte) << 8)
            for j in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc = crc & 0xffff
        return crc


class Field(object):
    def __init__(self, block_num, id, track_num, data):
        self.blockNumber = block_num
        self.id = id
        self.trackNumber = track_num
        # self.data is binary data.
        # For text fields, this is the binary, unencoded text
        self.data = data


class Block(object):
    def __init__(self, number):
        self.number = number
        self.__fields = {}

        self.__encoding = None
        self.__language = None

    def addField(self, field):
        assert(field.blockNumber == self.number)
        key = (field.id, field.trackNumber)

        if self.__fields.has_key(key):
            # No two fields should have the same ID and track number
            log.warning('duplicate CD-TEXT field: block %d, id %#x, track %d' %
                        (self.number,field.id, field.trackNumber))
            # For now, we'll continue and overwrite the old field
            pass

        self.__fields[key] = field

    def getField(self, id, track):
        key = (id, track)
        return self.__fields[key]

    @property
    def fields(self):
        return self.__fields.values()

    @property
    def encoding(self):
        if self.__encoding is None:
            self.__encoding = self.__getEncoding()
        return self.__encoding

    @property
    def language(self):
        if self.__language is None:
            self.__language = self.__getLanguage()
        return self.__language

    def getAlbumTitle(self):
        return self.getTextField(ID_TITLE, 0)

    def getTrackTitle(self, track_number):
        return self.getTextField(ID_TITLE, track_number, fallback=False)

    def getPerformer(self, track_number=0, fallback=True):
        return self.getTextField(ID_PERFORMER, track_number, fallback)

    def getSongWriter(self, track_number=0, fallback=True):
        return self.getTextField(ID_SONGWRITER, track_number, fallback)

    def getComposer(self, track_number=0, fallback=True):
        return self.getTextField(ID_COMPOSER, track_number, fallback)

    def getArranger(self, track_number=0, fallback=True):
        return self.getTextField(ID_ARRANGER, track_number, fallback)

    def getMessage(self, track_number=0, fallback=True):
        return self.getTextField(ID_MESSAGE, track_number, fallback)

    def getDiscId(self, track_number=0, fallback=True):
        return self.getTextField(ID_DISC_ID, track_number, fallback)

    def getGenre(self, track_number=0, fallback=True):
        return self.getTextField(ID_GENRE, track_number, fallback)

    def getISRC(self, track_number):
        return self.getTextField(ID_UPC_ISRC, track_number, fallback=False)

    def getUPC(self):
        return self.getTextField(ID_UPC_ISRC, 0)

    def getTextField(self, id, track_number, fallback=True):
        try:
            f = self.getField(id, track_number)
        except KeyError:
            if track_number != 0 and fallback:
                # If no track-specific info was specified,
                # fall back to the album info.
                f = self.getField(id, 0)
            else:
                return None

        return f.data.decode(self.encoding)

    def getTrackRange(self):
        """
        Returns a tuple of (first_track_num, last_track_num)
        """
        # The first and last track numbers ared stored in the Size Info pack
        # with track number 0
        try:
            size_info0 = self.getField(ID_SIZE_INFO, 0)
        except KeyError:
            raise CdTextError('missing Size Info pack 0 in block %d' %
                              (self.number,))

        return struct.unpack_from('BB', size_info0.data, 1)

    def __getEncoding(self):
        """
        Determine the character encoding for this block.

        Returns an encoding name that can be passed to str.decode()
        """
        # The character code is stored in the Size Info pack with
        # track number 0
        try:
            size_info0 = self.getField(ID_SIZE_INFO, 0)
        except KeyError:
            # Hmm.  No Size Info pack.  For now, just assume ASCII encoding
            log.warning('missing Size Info pack 0 in block %d' %
                        (self.number,))
            return 'ascii'

        (char_code,) = struct.unpack_from('B', size_info0.data, 0)

        try:
            return CHARACTER_CODES[char_code]
        except KeyError:
            raise CdTextError('unknown character code %#x for block %d' %
                              (char_code, self.number))

    def __getLanguage(self):
        """
        Determine the language of this block.

        Returns an encoding name that can be passed to str.decode()
        """
        # The language code is stored in the Size Info pack with
        # track number 2
        try:
            size_info2 = self.getField(ID_SIZE_INFO, 2)
        except KeyError:
            size_info2 = None

        if size_info2 is None:
            # Hmm.  No Size Info pack.
            log.warning('missing Size Info pack 2 in block %d' %
                        (self.number,))
            return LANGUAGE_UNKNOWN

        offset = 4 + self.number
        (lang_code,) = struct.unpack_from('B', size_info2.data, offset)
        return lang_code

    def validate(self):
        # INF-8090 says: "If Packs with Pack Type 80h to 85h, and 8Eh are used,
        # a character string for each track shall be provided."
        #
        # For each of these pack numbers, verify either that there are no packs
        # with this number, we have info for all tracks, or we have info for
        # track 0.
        # FIXME: implement this

        # FIXME: maybe we should also validate that we understand the character
        # code, and can decode all text fields correctly.
        pass


class Parser(object):
    def __init__(self, data):
        self.data = data
        self.idx = 0
        self.packSeq = 0
        self.pendingText = ''
        self.prevFieldText = None

        self.blocks = {}

    def parse(self):
        # Verify that the data is long enough.
        # Should consist of at least 4 bytes.
        if len(self.data) < 4:
            raise CdTextError('CD-TEXT data too short for header info '
                              '(length=%d)' % len(self.data))

        # Starts off with a 2 byte data length (big-endian).
        (cd_text_len,) = struct.unpack_from('>H', self.data, self.idx)
        self.idx += 2

        # Verify that we have as much data as specified by the length
        if len(self.data) < 2 + cd_text_len:
            raise CdTextError('specified CD-TEXT length (%d) is shorter than '
                              'supplied data (%d)' %
                              (cd_text_len, len(self.data) - 2))
        # The data should consist of 2 reserved bytes,
        # followed by a series of 18-byte packs.
        if cd_text_len < 2:
            raise CdTextError('specified CD-TEXT length (%d) is too short' %
                              (cd_text_len,))
        if (cd_text_len - 2) % 18 != 0:
            raise CdTextError('specified CD-TEXT length (%d) does not end on '
                              'a pack boundary' % (cd_text_len,))

        # Skip over the two reserved bytes
        self.idx += 2

        # Process the packs into fields
        while self.idx + 18 <= (2 + cd_text_len):
            pack = self.data[self.idx:self.idx+18]
            self.__parsePack(pack)
            self.idx += 18

        # Make sure everything looks sane
        for block in self.blocks.values():
            block.validate()

        return CdText(self.blocks.values())

    def __parsePack(self, pack_data):
        # Parse and verify the pack data
        pack = Pack(pack_data, self.packSeq)
        self.packSeq += 1

        # Process the text data in the pack
        self.__handlePack(pack)

    def __handlePack(self, pack):
        if pack.dbcc:
            # FIXME: handle DBCC properly
            raise NotImplementedError('double-byte characters in pack')

        # The MMC-2/MMC-3 docs have the following to say about the track
        # number: "The MSB of this byte [is] the Extension Flag and is normally
        # set to 0b.  If it is set to 1b, the Pack is used for an extended
        # application that is beyond the scope of this document."
        if pack.trackNumber & 0b10000000:
            raise CdTextError('unable to handle pack with extension flag '
                              '(pack id=%#x, seq=%d)' % (pack.id, pack.seqNum))

        # Switch based on whether or not the pack contains binary data
        # or a character string.
        #
        # XXX: One paragraph of MMC-3 (and INF-8090) says all packs contain
        # character data except those with IDs of 0x88, 0x89, or 0x8f.
        # However, 4 paragraphs later it says IDs 0x86, 0x87, 0x88, 0x89, and
        # 0x8f contain binary data.  (I've seen CDs with 0x86 packs, and it
        # appears to be text data.)
        if pack.id == ID_TOC or pack.id == ID_TOC2 or pack.id == ID_SIZE_INFO:
            self.__handleBinaryPack(pack)
        else:
            self.__handleTextPack(pack)

    def __handleBinaryPack(self, pack):
        # There shouldn't have been any previous unfinished character data.
        if self.pendingText:
            raise CdTextError('binary pack (id=%#x, seq=%d) followed pack '
                              'with unterminated character data' %
                              (pack.id, pack.seqNum))

        # INF-8090 states character position should be 0 for these
        # pack types.
        if pack.charPosition != 0:
            raise CdTextError('binary pack (id=%#x, seq=%d) contains non-zero '
                              'character position %d' %
                              (pack.id, pack.seqNum, pack.charPosition))

        field = Field(pack.blockNumber, pack.id, pack.trackNumber, pack.value)
        self.__addField(field)

    def __handleTextPack(self, pack):
        strings = pack.value.split('\0')

        # XXX: Should we use pack.charPosition in the following code?
        # It doesn't really seem to be very useful.

        for data in strings[:-1]:
            full_text = self.pendingText + data
            self.__handleTextField(full_text, pack)
            self.pendingText = ''

        self.pendingText += strings[-1]

    def __handleTextField(self, text, pack):
        # Some packs are padded with NUL bytes.
        # Ignore text if it is empty
        if not text:
            return

        # According to SFF 8090, if the text is '\t' (or '\t\t' if pack.dbcc
        # is True), we should use the text from the previous field
        use_previous = False
        if pack.dbcc:
            use_previous = (text == '\t\t')
        else:
            use_previous = (text == '\t')
        if use_previous:
            if self.prevFieldText is None:
                raise CdTextError('pack %d (id=%#x) indicates to use previous '
                                  'text value, but no previous value is '
                                  'available' % (pack.seqNum, pack.id))
            text = self.prevFieldText
        else:
            self.prevFieldText = text

        # Just store the field for now.
        # We will decode the text to unicode once we have parsed
        # the encoding from the "Size Info" packs
        field = Field(pack.blockNumber, pack.id, pack.trackNumber, text)
        self.__addField(field)

    def __addField(self, field):
        try:
            block = self.blocks[field.blockNumber]
        except KeyError, ex:
            block = Block(field.blockNumber)
            self.blocks[field.blockNumber] = block

        block.addField(field)


def parse(data):
    parser = Parser(data)
    return parser.parse()


def read_cd_text(device):
    data = binary.read_cd_text(device)
    return parse(data)
