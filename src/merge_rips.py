#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
"""
Merge several different ripped versions of a track.  Useful when cdparanoia
reports some uncorrectable errors.  If you have ripped the track several times,
this tool can merge them all, by choosing the most popular value from all files
for each byte value.

Usage: merge.py FILE1 FILE2 [...] > merged.wav
"""

import sys

def msg(s):
    print >> sys.stderr, str(s)


def handle_difference(outf, bytes, offset):
    values = {}
    for b in bytes:
        try:
            values[b] += 1
        except KeyError:
            values[b] = 1

    max_count = 0
    max_byte = []
    for (b, count) in values.items():
        if count > max_count:
            max_count = count
            max_byte = [b]
        elif count == max_count:
            max_byte.append(b)

    if len(max_byte) != 1:
        raise Exception('tie at offset %d: %s' % (offset, max_byte))

    msg('%d: %s --> %r' % (offset, values, max_byte[0]))
    outf.write(max_byte[0])


def handle_chunks(outf, chunks, offset):
    # See if there are any differences
    v = chunks[0]
    for c in chunks:
        if c != v:
            break
    else:
        # Great, all identical
        outf.write(v)
        sys.stderr.write('%d\r' % (offset,))
        return

    # Hmm.  We found differences.
    # Try to split the chunks in half, and recurse on each half.
    l = len(v)
    if l == 1:
        # Down to single byte chunks.
        # Handle the difference.
        handle_difference(outf, chunks, offset)
    else:
        h = l / 2
        first_half = [c[:h] for c in chunks]
        second_half = [c[h:] for c in chunks]
        handle_chunks(outf, first_half, offset)
        handle_chunks(outf, second_half, offset + h)


def main(argv):
    filenames = argv[1:]
    msg(filenames)

    outf = sys.stdout

    files = [open(name, 'r') for name in filenames]

    block_size = 2048
    offset = 0
    while True:
        blocks = [f.read(block_size) for f in files]

        # FIXME: detect end of file better.
        # If some end before others, handle the error.
        if not blocks[0]:
            break

        handle_chunks(outf, blocks, offset)
        offset += block_size

    return 0


if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
