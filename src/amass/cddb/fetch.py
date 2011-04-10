#!/usr/bin/python -tt
#
# Copyright (c) 2011, Adam Simpkins
#
import os

from .. import file_util
from . import cddbp


def fetch_cddb(toc, dir):
    # Create the cddb directory.
    # For now, just fail if it already exists
    cddb_dir = dir.layout.getCddbDir()
    os.makedirs(cddb_dir)

    # Query CDDB for entries for this disc
    results = cddbp.query_cddb(toc)

    # Store each match in the CDDB directory
    for (category, data) in results.iteritems():
        path = os.path.join(cddb_dir, category)
        print 'Writing %s' % (path,)
        data_file = file_util.open_new(path)
        data_file.write(data.encode('UTF-8'))
        data_file.close()
