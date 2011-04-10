#!/usr/bin/python -tt
#
# Copyright (c) 2011, Adam Simpkins
#
from .. import file_util
from . import query_toc_raw


def fetch_mb(toc, dir):
    # Query raw data from MusicBrainz
    mb_data = query_toc_raw(toc)

    mb_path = dir.layout.getMusicBrainzPath()
    print 'Writing %s' % (mb_path,)
    mb_file = file_util.open_new(mb_path)
    mb_file.write(mb_data)
    mb_file.close()
