#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#

# There are 75 frames per second
# (ECMA-130 section 21)
FRAMES_PER_SECOND = 75
SECONDS_PER_MINUTE = 60

# MSF numbering offset of the first frame
MSF_OFFSET = FRAMES_PER_SECOND * 2

# Number of 16-bit samples per frame.
# (Divide by 2 to get number of stereo samples)
SAMPLES_PER_FRAME = 1176

# The leadout info is stored in the TOC as track number 0xAA
TRACK_LEADOUT = 0xAA

# Control flags
CTRL_4CHANNELS    = 0x08 # 4-channel audio instead of 2-channel
                         # (should be unset for data tracks)
CTRL_DATA_TRACK   = 0x04 # indicates a data track
CTRL_COPY_ALLOWED = 0x02 # set if digital copy permitted
CTRL_PREEMPHASIS  = 0x01 # if audio track, pre-emphasis is enabled

# ADR field values
ADR_NOT_SPECIFIED       = 0
ADR_POSITION            = 1
ADR_CATALOG_NUMBER      = 2
ADR_ISRC                = 3

# Disc type field values
DISC_TYPE_CD            = 0x00 # CD-DA or CD-ROM
DISC_TYPE_CD_I          = 0x10
DISC_TYPE_CD_XA         = 0x20
DISC_TYPE_DVD_ROM       = 0x40
DISC_TYPE_DVD_RAM       = 0x80
