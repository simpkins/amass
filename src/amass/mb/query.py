#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import musicbrainz2.disc as mbdisc
import musicbrainz2.webservice as mbws

from . import disc_id as mb_did


def query_disc_id(disc_id):
    ws = mbws.WebService()
    query = mbws.Query(ws)

    try:
        filter = mbws.ReleaseFilter(discId=disc_id)
        results = query.getReleases(filter)
    except mbws.WebServiceError, ex:
        # FIXME
        raise

    return results

def query_disc_id_raw(disc_id):
    ws = mbws.WebService()

    include_params = []

    filter = mbws.ReleaseFilter(discId=disc_id)
    filter_params = filter.createParameters()

    try:
        stream = ws.get('release', '', include_params, filter_params)
    except mbws.WebServiceError, ex:
        # FIXME
        raise

    buf = stream.read()
    return buf


def query_toc(toc):
    disc_id = mb_did.get_mb_id(toc)
    return query_disc_id(disc_id)


def query_toc_raw(toc):
    disc_id = mb_did.get_mb_id(toc)
    return query_disc_id_raw(disc_id)
