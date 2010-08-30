#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#

# Test TOC buffers
# from Philip Glass's Glassworks, Expanded Edition
FULL_TOC_GLASSWORKS = \
        '\x00\x9c\x01\x01' \
        '\x01\x10\x00\xa0\x00\x00\x00\x00\x01\x00\x00' \
        '\x01\x10\x00\xa1\x00\x00\x00\x00\x0b\x00\x00' \
        '\x01\x10\x00\xa2\x00\x00\x00\x00\x3f\x03\x00' \
        '\x01\x10\x00\x01\x00\x00\x00\x00\x00\x02\x00' \
        '\x01\x10\x00\x02\x00\x00\x00\x00\x06\x1a\x43' \
        '\x01\x10\x00\x03\x00\x00\x00\x00\x0c\x1a\x1e' \
        '\x01\x10\x00\x04\x00\x00\x00\x00\x14\x06\x39' \
        '\x01\x10\x00\x05\x00\x00\x00\x00\x1a\x0b\x19' \
        '\x01\x10\x00\x06\x00\x00\x00\x00\x21\x20\x28' \
        '\x01\x10\x00\x07\x00\x00\x00\x00\x27\x24\x16' \
        '\x01\x10\x00\x08\x00\x00\x00\x00\x28\x2e\x43' \
        '\x01\x10\x00\x09\x00\x00\x00\x00\x2e\x1d\x19' \
        '\x01\x10\x00\x0a\x00\x00\x00\x00\x31\x36\x1b' \
        '\x01\x10\x00\x0b\x00\x00\x00\x00\x36\x34\x16'

# Glassworks simple TOC, requested in LBA mode
SIMPLE_TOC_GLASSWORKS = \
        '\x00\x62\x01\x0b' \
        '\x00\x10\x01\x00\x00\x00\x00\x00' \
        '\x00\x10\x02\x00\x00\x00\x70\xc3' \
        '\x00\x10\x03\x00\x00\x00\xda\x16' \
        '\x00\x10\x04\x00\x00\x01\x60\xf5' \
        '\x00\x10\x05\x00\x00\x01\xcb\xc4' \
        '\x00\x10\x06\x00\x00\x02\x4d\x06' \
        '\x00\x10\x07\x00\x00\x02\xb7\x98' \
        '\x00\x10\x08\x00\x00\x02\xcc\x47' \
        '\x00\x10\x09\x00\x00\x03\x30\x9a' \
        '\x00\x10\x0a\x00\x00\x03\x6c\xab' \
        '\x00\x10\x0b\x00\x00\x03\xc3\xf4' \
        '\x00\x10\xaa\x00\x00\x04\x53\xb7'

CD_TEXT_GLASSWORKS = \
    '\x03\x50\x00\x00' \
    '\x80\x00\x00\x00\x47\x6c\x61\x73\x73\x77\x6f\x72\x6b\x73\x20\x2d\x8e\xd0'\
    '\x80\x00\x01\x0c\x20\x45\x78\x70\x61\x6e\x64\x65\x64\x20\x45\x64\xfc\x47'\
    '\x80\x00\x02\x0f\x69\x74\x69\x6f\x6e\x00\x47\x6c\x61\x73\x73\x77\x51\xd5'\
    '\x80\x01\x03\x06\x6f\x72\x6b\x73\x3a\x20\x4f\x70\x65\x6e\x69\x6e\x84\x70'\
    '\x80\x01\x04\x0f\x67\x00\x47\x6c\x61\x73\x73\x77\x6f\x72\x6b\x73\x38\x2d'\
    '\x80\x02\x05\x0a\x3a\x20\x46\x6c\x6f\x65\x00\x47\x6c\x61\x73\x73\x5e\x69'\
    '\x80\x03\x06\x05\x77\x6f\x72\x6b\x73\x3a\x20\x49\x73\x6c\x61\x6e\x97\x86'\
    '\x80\x03\x07\x0f\x64\x73\x00\x47\x6c\x61\x73\x73\x77\x6f\x72\x6b\xce\x79'\
    '\x80\x04\x08\x09\x73\x3a\x20\x52\x75\x62\x72\x69\x63\x00\x47\x6c\xe9\x3e'\
    '\x80\x05\x09\x02\x61\x73\x73\x77\x6f\x72\x6b\x73\x3a\x20\x46\x61\x19\xb0'\
    '\x80\x05\x0a\x0e\x63\x61\x64\x65\x73\x00\x47\x6c\x61\x73\x73\x77\x07\x91'\
    '\x80\x06\x0b\x06\x6f\x72\x6b\x73\x3a\x20\x43\x6c\x6f\x73\x69\x6e\xfa\x87'\
    '\x80\x06\x0c\x0f\x67\x00\x49\x6e\x20\x54\x68\x65\x20\x55\x70\x70\x5d\xc2'\
    '\x80\x07\x0d\x0a\x65\x72\x20\x52\x6f\x6f\x6d\x3a\x20\x44\x61\x6e\x43\xc5'\
    '\x80\x07\x0e\x0f\x63\x65\x20\x49\x00\x49\x6e\x20\x54\x68\x65\x20\xa7\x03'\
    '\x80\x08\x0f\x07\x55\x70\x70\x65\x72\x20\x52\x6f\x6f\x6d\x3a\x20\xc2\x72'\
    '\x80\x08\x10\x0f\x44\x61\x6e\x63\x65\x20\x49\x49\x00\x49\x6e\x20\x29\xf3'\
    '\x80\x09\x11\x03\x54\x68\x65\x20\x55\x70\x70\x65\x72\x20\x52\x6f\x2d\x99'\
    '\x80\x09\x12\x0f\x6f\x6d\x3a\x20\x44\x61\x6e\x63\x65\x20\x56\x00\x69\xe1'\
    '\x80\x0a\x13\x00\x49\x6e\x20\x54\x68\x65\x20\x55\x70\x70\x65\x72\x6d\x0e'\
    '\x80\x0a\x14\x0c\x20\x52\x6f\x6f\x6d\x3a\x20\x44\x61\x6e\x63\x65\x1b\x94'\
    '\x80\x0a\x15\x0f\x20\x56\x49\x49\x49\x00\x49\x6e\x20\x54\x68\x65\x08\x41'\
    '\x80\x0b\x16\x06\x20\x55\x70\x70\x65\x72\x20\x52\x6f\x6f\x6d\x3a\x66\x3d'\
    '\x80\x0b\x17\x0f\x20\x44\x61\x6e\x63\x65\x20\x49\x58\x00\x00\x00\x63\xeb'\
    '\x81\x00\x18\x00\x50\x68\x69\x6c\x69\x70\x20\x47\x6c\x61\x73\x73\x4d\x0a'\
    '\x81\x00\x19\x0c\x20\x45\x6e\x73\x65\x6d\x62\x6c\x65\x2c\x20\x50\xc0\x3d'\
    '\x81\x00\x1a\x0f\x68\x69\x6c\x69\x70\x20\x47\x6c\x61\x73\x73\x2c\x17\x90'\
    '\x81\x00\x1b\x0f\x20\x4d\x69\x63\x68\x61\x65\x6c\x20\x52\x65\x69\x9c\x0d'\
    '\x81\x00\x1c\x0f\x73\x6d\x61\x6e\x00\x00\x00\x00\x00\x00\x00\x00\xa5\xc1'\
    '\x81\x08\x1d\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd3\xb7'\
    '\x86\x00\x1e\x00\x53\x4b\x39\x30\x33\x39\x34\x00\x00\x00\x00\x00\xc9\xb2'\
    '\x8e\x00\x1f\x00\x30\x37\x34\x36\x34\x33\x37\x32\x36\x35\x32\x38\xcc\x93'\
    '\x8e\x00\x20\x0c\x00\x55\x53\x53\x4d\x31\x38\x31\x30\x30\x33\x38\x90\xb6'\
    '\x8e\x01\x21\x0b\x35\x00\x55\x53\x53\x4d\x31\x30\x30\x31\x35\x32\x98\xeb'\
    '\x8e\x02\x22\x0a\x31\x33\x00\x55\x53\x53\x4d\x31\x38\x31\x30\x30\xfc\xba'\
    '\x8e\x03\x23\x09\x33\x38\x36\x00\x55\x53\x53\x4d\x31\x38\x31\x30\x4d\x45'\
    '\x8e\x04\x24\x08\x30\x33\x38\x37\x00\x55\x53\x53\x4d\x31\x30\x30\xea\xeb'\
    '\x8e\x05\x25\x07\x31\x35\x32\x31\x34\x00\x55\x53\x53\x4d\x31\x38\x33\x21'\
    '\x8e\x06\x26\x06\x31\x30\x30\x33\x38\x38\x00\x55\x53\x53\x4d\x31\x28\xdf'\
    '\x8e\x07\x27\x05\x38\x37\x30\x30\x36\x31\x39\x00\x55\x53\x53\x4d\x72\xeb'\
    '\x8e\x08\x28\x04\x31\x38\x37\x30\x30\x36\x32\x30\x00\x55\x53\x53\xa2\xc1'\
    '\x8e\x09\x29\x03\x4d\x31\x38\x37\x30\x30\x36\x32\x31\x00\x55\x53\x14\x87'\
    '\x8e\x0a\x2a\x02\x53\x4d\x31\x38\x37\x30\x30\x34\x38\x39\x00\x55\x53\x16'\
    '\x8e\x0b\x2b\x01\x53\x53\x4d\x31\x38\x37\x30\x30\x36\x32\x32\x00\xc7\xc6'\
    '\x8f\x00\x2c\x00\x01\x01\x0b\x00\x18\x06\x00\x00\x00\x00\x01\x00\x94\x57'\
    '\x8f\x01\x2d\x00\x00\x00\x00\x00\x00\x00\x0d\x03\x2e\x00\x00\x00\xe5\x8d'\
    '\x8f\x02\x2e\x00\x00\x00\x00\x00\x09\x00\x00\x00\x00\x00\x00\x00\xe7\x87'

# Full TOC from "Karmacode" by Lacuna Coil
# This is a CD-XA disc (2 sessions, last one contains a single data track)
FULL_TOC_KARMACODE = \
    '\x00\xf4\x01\x02' \
    '\x01\x10\x00\xa0\x00\x00\x00\x00\x01\x00\x00' \
    '\x01\x10\x00\xa1\x00\x00\x00\x00\x0d\x00\x00' \
    '\x01\x10\x00\xa2\x00\x00\x00\x00\x2f\x1d\x08' \
    '\x01\x10\x00\x01\x00\x00\x00\x00\x00\x02\x00' \
    '\x01\x10\x00\x02\x00\x00\x00\x00\x04\x1c\x3c' \
    '\x01\x10\x00\x03\x00\x00\x00\x00\x07\x32\x36' \
    '\x01\x10\x00\x04\x00\x00\x00\x00\x0b\x35\x3f' \
    '\x01\x10\x00\x05\x00\x00\x00\x00\x0f\x20\x39' \
    '\x01\x10\x00\x06\x00\x00\x00\x00\x13\x19\x25' \
    '\x01\x10\x00\x07\x00\x00\x00\x00\x14\x39\x41' \
    '\x01\x10\x00\x08\x00\x00\x00\x00\x18\x26\x49' \
    '\x01\x10\x00\x09\x00\x00\x00\x00\x1c\x31\x30' \
    '\x01\x10\x00\x0a\x00\x00\x00\x00\x1f\x33\x1b' \
    '\x01\x10\x00\x0b\x00\x00\x00\x00\x23\x33\x00' \
    '\x01\x10\x00\x0c\x00\x00\x00\x00\x27\x17\x3a' \
    '\x01\x10\x00\x0d\x00\x00\x00\x00\x2b\x17\x27' \
    '\x01\x50\x00\xb0\x31\x3b\x08\x02\x38\x33\x48' \
    '\x01\x50\x00\xc0\x00\x00\x00\x00\x5f\x00\x00' \
    '\x02\x14\x00\xa0\x00\x00\x00\x00\x0e\x20\x00' \
    '\x02\x14\x00\xa1\x00\x00\x00\x00\x0e\x00\x00' \
    '\x02\x14\x00\xa2\x00\x00\x00\x00\x38\x33\x48' \
    '\x02\x14\x00\x0e\x00\x00\x00\x00\x32\x01\x08'

# Full TOC from "Dusk and Summer" by Dashboard Confessional
# Interesting because it has "hidden" audio data before the first track.
# The first track
FULL_TOC_DUSK_AND_SUMMER = \
    '\x00\x91\x01\x01' \
    '\x01\x10\x00\xa0\x00\x00\x00\x00\x01\x00\x00' \
    '\x01\x10\x00\xa1\x00\x00\x00\x00\x0a\x00\x00' \
    '\x01\x10\x00\xa2\x00\x00\x00\x00\x32\x19\x2e' \
    '\x01\x10\x00\x01\x00\x00\x00\x00\x09\x2e\x32' \
    '\x01\x10\x00\x02\x00\x00\x00\x00\x0d\x33\x33' \
    '\x01\x10\x00\x03\x00\x00\x00\x00\x11\x22\x3f' \
    '\x01\x10\x00\x04\x00\x00\x00\x00\x14\x3b\x0d' \
    '\x01\x10\x00\x05\x00\x00\x00\x00\x18\x34\x26' \
    '\x01\x10\x00\x06\x00\x00\x00\x00\x1c\x2f\x19' \
    '\x01\x10\x00\x07\x00\x00\x00\x00\x21\x03\x13' \
    '\x01\x10\x00\x08\x00\x00\x00\x00\x25\x1e\x28' \
    '\x01\x10\x00\x09\x00\x00\x00\x00\x29\x27\x0d' \
    '\x01\x10\x00\x0a\x00\x00\x00\x00\x2e\x11\x25'


# CD-TEXT data from "Wonder What's Next" by Chevelle
# Interesting because the title info for track 8 doesn't get its own pack.
# It appears in the middle of a pack whose's header indicates that it starts
# with track 7 title info.
CD_TEXT_WONDER_WHATS_NEXT = \
    '\x03\x1a\x00\x00' \
    '\x80\x00\x00\x00\x57\x6f\x6e\x64\x65\x72\x20\x57\x68\x61\x74\x27\xe0\x58'\
    '\x80\x00\x01\x0c\x73\x20\x4e\x65\x78\x74\x00\x46\x61\x6d\x69\x6c\xb0\x12'\
    '\x80\x01\x02\x05\x79\x20\x53\x79\x73\x74\x65\x6d\x00\x43\x6f\x6d\x1c\xae'\
    '\x80\x02\x03\x03\x66\x6f\x72\x74\x61\x62\x6c\x65\x20\x4c\x69\x61\xf6\x79'\
    '\x80\x02\x04\x0f\x72\x00\x53\x65\x6e\x64\x20\x54\x68\x65\x20\x50\xe4\x80'\
    '\x80\x03\x05\x0a\x61\x69\x6e\x20\x42\x65\x6c\x6f\x77\x00\x43\x6c\x9f\xe9'\
    '\x80\x04\x06\x02\x6f\x73\x75\x72\x65\x00\x54\x68\x65\x20\x52\x65\x61\xf6'\
    '\x80\x05\x07\x06\x64\x00\x57\x6f\x6e\x64\x65\x72\x20\x57\x68\x61\x2f\xe3'\
    '\x80\x06\x08\x0a\x74\x27\x73\x20\x4e\x65\x78\x74\x00\x44\x6f\x6e\xa1\x30'\
    '\x80\x07\x09\x03\x27\x74\x20\x46\x61\x6b\x65\x20\x54\x68\x69\x73\x34\x61'\
    '\x80\x07\x0a\x0f\x00\x46\x6f\x72\x66\x65\x69\x74\x00\x47\x72\x61\x58\xec'\
    '\x80\x09\x0b\x03\x62\x20\x54\x68\x79\x20\x48\x61\x6e\x64\x00\x41\xe5\xa3'\
    '\x80\x0a\x0c\x01\x6e\x20\x45\x76\x65\x6e\x69\x6e\x67\x20\x57\x69\xe7\x0e'\
    '\x80\x0a\x0d\x0d\x74\x68\x20\x45\x6c\x20\x44\x69\x61\x62\x6c\x6f\x49\xff'\
    '\x80\x0a\x0e\x0f\x00\x4f\x6e\x65\x20\x4c\x6f\x6e\x65\x6c\x79\x20\xab\x1e'\
    '\x80\x0b\x0f\x0b\x56\x69\x73\x69\x74\x6f\x72\x00\x00\x00\x00\x00\x05\xc3'\
    '\x81\x00\x10\x00\x43\x68\x65\x76\x65\x6c\x6c\x65\x00\x43\x68\x65\xc5\xed'\
    '\x81\x01\x11\x03\x76\x65\x6c\x6c\x65\x00\x43\x68\x65\x76\x65\x6c\x26\xdb'\
    '\x81\x02\x12\x06\x6c\x65\x00\x43\x68\x65\x76\x65\x6c\x6c\x65\x00\xba\x91'\
    '\x81\x04\x13\x00\x43\x68\x65\x76\x65\x6c\x6c\x65\x00\x43\x68\x65\xd3\xfc'\
    '\x81\x05\x14\x03\x76\x65\x6c\x6c\x65\x00\x43\x68\x65\x76\x65\x6c\x3b\xad'\
    '\x81\x06\x15\x06\x6c\x65\x00\x43\x68\x65\x76\x65\x6c\x6c\x65\x00\x51\x25'\
    '\x81\x08\x16\x00\x43\x68\x65\x76\x65\x6c\x6c\x65\x00\x43\x68\x65\xe9\xcf'\
    '\x81\x09\x17\x03\x76\x65\x6c\x6c\x65\x00\x43\x68\x65\x76\x65\x6c\x0a\xf9'\
    '\x81\x0a\x18\x06\x6c\x65\x00\x43\x68\x65\x76\x65\x6c\x6c\x65\x00\x80\x7d'\
    '\x86\x00\x19\x00\x45\x4b\x38\x36\x31\x35\x37\x00\x00\x00\x00\x00\xa3\x3a'\
    '\x8e\x00\x1a\x00\x00\x55\x53\x2d\x53\x4d\x31\x2d\x30\x32\x2d\x30\x7d\x54'\
    '\x8e\x01\x1b\x0b\x31\x35\x32\x37\x00\x55\x53\x2d\x53\x4d\x31\x2d\x80\x02'\
    '\x8e\x02\x1c\x07\x30\x32\x2d\x30\x31\x35\x32\x38\x00\x55\x53\x2d\xa2\x5f'\
    '\x8e\x03\x1d\x03\x53\x4d\x31\x2d\x30\x32\x2d\x30\x31\x35\x32\x39\xa2\x31'\
    '\x8e\x03\x1e\x0f\x00\x55\x53\x2d\x53\x4d\x31\x2d\x30\x32\x2d\x30\xa2\x86'\
    '\x8e\x04\x1f\x0b\x31\x35\x33\x30\x00\x55\x53\x2d\x53\x4d\x31\x2d\x96\x07'\
    '\x8e\x05\x20\x07\x30\x32\x2d\x30\x31\x35\x33\x31\x00\x55\x53\x2d\x7a\xe2'\
    '\x8e\x06\x21\x03\x53\x4d\x31\x2d\x30\x32\x2d\x30\x31\x35\x33\x32\x58\xd3'\
    '\x8e\x06\x22\x0f\x00\x55\x53\x2d\x53\x4d\x31\x2d\x30\x32\x2d\x30\xda\x3e'\
    '\x8e\x07\x23\x0b\x31\x35\x33\x33\x00\x55\x53\x2d\x53\x4d\x31\x2d\x15\x90'\
    '\x8e\x08\x24\x07\x30\x32\x2d\x30\x31\x35\x33\x34\x00\x55\x53\x2d\xb6\x1b'\
    '\x8e\x09\x25\x03\x53\x4d\x31\x2d\x30\x32\x2d\x30\x31\x35\x33\x35\x8a\x43'\
    '\x8e\x09\x26\x0f\x00\x55\x53\x2d\x53\x4d\x31\x2d\x30\x32\x2d\x30\x78\x49'\
    '\x8e\x0a\x27\x0b\x31\x35\x33\x36\x00\x55\x53\x2d\x53\x4d\x31\x2d\x8d\xf2'\
    '\x8e\x0b\x28\x07\x30\x32\x2d\x30\x31\x35\x33\x37\x00\x00\x00\x00\xb6\x3f'\
    '\x8f\x00\x29\x00\x01\x01\x0b\x03\x10\x09\x00\x00\x00\x00\x01\x00\xab\xe4'\
    '\x8f\x01\x2a\x00\x00\x00\x00\x00\x00\x00\x0f\x03\x2b\x00\x00\x00\xa2\x8e'\
    '\x8f\x02\x2b\x00\x00\x00\x00\x00\x09\x00\x00\x00\x00\x00\x00\x00\x61\x43'
