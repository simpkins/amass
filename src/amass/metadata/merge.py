#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
from . import fields
from . import track

from .. import cdrom


class Source(object):
    """
    A Source object represents the source of information for album metadata.

    e.g., freedb.org, MusicBrainz, CD-TEXT, etc.
    """
    def __init__(self, name, score=100):
        self.name = name
        self.score = score

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Source(%r)' % (self.name,)


class DataSourceBase(Source):
    """
    A base class for Source classes that contain metadata information.
    """
    def updateTrack(self, track):
        raise NotImplementedError('updateTrack() must be implemented by '
                                  'DataSourceBase subclasses')

    def updateField(self, field, value):
        if field.candidates is None:
            field.candidates = CandidateList(field)
        field.candidates.addCandidate(value, self)


class CddbSource(DataSourceBase):
    """
    A metadata source from a CDDB entry.
    """
    def __init__(self, entry, name, score=None):
        # I haven't been thrilled with the quality of CDDB results in the past.
        # Give CDDB sources a slightly lower score than the default
        if score is None:
            score = 90

        DataSourceBase.__init__(self, name)
        self.entry = entry

    def updateTrack(self, track):
        num = track.number
        self.updateField(track.album, self.entry.getTitle())
        self.updateField(track.trackTitle, self.entry.getTrackTitle(num))
        self.updateField(track.artist, self.entry.getTrackArtist(num))
        self.updateField(track.genre, self.entry.getGenre())
        self.updateField(track.releaseYear, self.entry.getYear())


class MbSource(DataSourceBase):
    """
    A metadata source from a MusicBrainz entry.
    """
    def __init__(self, release_result, name, score=None):
        if score is None:
            # MB scores are between 0 and 100
            # We use this value as-is for now.
            score = release_result.getScore()

        DataSourceBase.__init__(self, name, score)
        self.release = release_result.getRelease()

    def __getTrack(self, track_num):
        offset = self.release.getTracksOffset()
        if offset is None:
            offset = 0

        # Subtract 1, since track 1 is normally at index 0
        # (assuming the offset is 0)
        return self.release.getTracks()[offset + track_num - 1]

    def updateTrack(self, track):
        try:
            mb_track = self.__getTrack(track.number)
        except IndexError:
            # Do nothing if there is no MusicBrainz info for this track
            # (For example, this may occur if this is a data track.)
            return

        self.updateField(track.album, self.release.getTitle())
        self.updateField(track.trackTitle, mb_track.getTitle())

        mb_artist = mb_track.getArtist()
        if mb_artist is None:
            mb_artist = self.release.getArtist()
        self.updateField(track.artist, mb_artist.getName())
        # TODO: make sure the query parameters we send to musicbrainz
        # actually requests that artist sort names be returned.
        self.updateField(track.artistSortName, mb_artist.getSortName())

        try:
            isrcs = mb_track.getISRCs()
        except AttributeError:
            # getISRCs() isn't present in older musicbrainz2 code
            isrcs = []
        for isrc in isrcs:
            self.updateField(track.isrc, isrc)

        # TODO: prefer a US release event:
        for event in self.release.getReleaseEvents():
            # FIXME: Disabled for now since we need more testing
            # - date
            # - catalog number
            # - barcode
            # - label
            pass


class CdTextSource(DataSourceBase):
    """
    A metadata source from a CD-TEXT block.
    """
    def __init__(self, block, score=None):
        if score is None:
            # CD-TEXT information is provided by the publisher.
            # Treat it as more valuable than CDDB or MusicBrainz info.
            # (However, this score still means that if 2 CDDB or MusicBrainz
            # sources agree on a different value, they will be preferred.)
            score = 170
        name = 'CD-TEXT %s' % (cdrom.cdtext.LANGUAGE_NAMES[block.language],)

        DataSourceBase.__init__(self, name, score)
        self.block = block

    def updateTrack(self, track):
        num = track.number
        self.updateField(track.album, self.block.getAlbumTitle())
        self.updateField(track.trackTitle, self.block.getTrackTitle(num))


# TODO: Add a source to add the ISRC codes from the stored icedax data
class TocSource(Source):
    """
    A metadata source that represents information from the
    CD Table of Contents.

    This source is mainly used for things like track numbers.
    """
    def __init__(self):
        Source.__init__(self, 'CD TOC', 10000)


class Candidate(object):
    """
    One possible candidate for a field value.

    A candidate contains the value, and all sources that have suggested this
    value.
    """
    def __init__(self, value):
        self.value = value
        self.sources = []
        self.score = 0

    def addSource(self, source):
        self.sources.append(source)
        self.score += source.score


class PreferredChoice(object):
    def __init__(self, value, sources, confidence):
        self.value = value
        # Note: these sources may not have exactly specified this value;
        # the value may have been canonicalized.
        self.sources = sources[:]
        self.confidence = confidence


class CandidateList(object):
    """
    A metadata field containing information from various sources.
    """
    def __init__(self, field):
        self.candidates = {}
        self.field = field
        self.preferredChoice = None

    def __nonzero__(self):
        return bool(self.candidates)

    def addCandidate(self, value, source):
        # TODO: check self.field.coerce() and self.field.validate()?
        try:
            candidate = self.candidates[value]
        except KeyError:
            candidate = Candidate(value)
            self.candidates[value] = candidate

        candidate.addSource(source)

    def groupCandidates(self, candidates, squash):
        groups = {}
        for candidate in candidates:
            squashed = squash(candidate.value)
            if groups.has_key(squashed):
                groups[squashed].append(candidate)
            else:
                groups[squashed] = [candidate]

        return groups

    def chooseGroup(self, groups):
        max_sources = -1
        preferred_candidates = []
        for (value, candidates) in groups.iteritems():
            num_sources = 0
            for candidate in candidates:
                num_sources += len(candidate.sources)
            if num_sources > max_sources:
                max_sources = num_sources
                preferred_candidates = candidates[:]
            elif num_sources == max_sources:
                # If there is a tie between multiple groups,
                # return the candidates from all tied groups.
                preferred_candidates.extend(candidates)

        return preferred_candidates

    def rateCandidates(self):
        if not self.candidates:
            # Nothing to do if there are no candidates
            # Leave self.preferredChoice as None
            return

        for candidate in self.candidates.itervalues():
            candidate.score = self.field.computeScore(candidate.value)

        self.preferredChoice = self.computePreferredChoice()
        self.preferredChoice.score = \
                self.field.computeScore(self.preferredChoice.value)

    def computePreferredChoice(self):
        # Start out with 100% confidence in our choice.
        # We subtract confidence as we eliminate candidates
        confidence = 100

        # First group according to self.field.squash(), and choose the groups
        # that have the most sources that agree on the squashed value.
        # squash() strips away hopefully meaningless differences, to find
        # all candidates which roughly agree.
        #
        # This step throws out candidates that substantially differ from the
        # majority of other candidates.
        squashed_groups = self.groupCandidates(self.candidates.values(),
                                               self.field.squash)
        post_squash_candidates = self.chooseGroup(squashed_groups)
        if len(post_squash_candidates) != len(self.candidates):
            confidence -= 5

        # Among the candidates from the preferred squashed group,
        # now group according to self.field.canonicalize(), and again choose
        # the groups with the most sources that agree.
        canonical_groups = self.groupCandidates(post_squash_candidates,
                                                self.field.canonicalize)
        post_canon_candidates = self.chooseGroup(canonical_groups)
        if len(post_canon_candidates) != len(post_squash_candidates):
            confidence -= 5

        # TODO: This step should be eliminated; we should have
        # enough information to remember this from when we group by
        # self.field.canonicalize()
        canonical_values = {}
        for candidate in post_canon_candidates:
            cvalue = self.field.canonicalize(candidate.value)
            if canonical_values.has_key(cvalue):
                canonical_values[cvalue].extend(candidate.sources)
            else:
                canonical_values[cvalue] = candidate.sources[:]

        if len(post_canon_candidates) == 1:
            # All candidates are exactly the same.
            candidate = post_canon_candidates[0]
            assert len(canonical_values) == 1
            cvalue = canonical_values.iterkeys().next()

            if candidate.value == cvalue:
                # The value is also in canonical form
                # Return it, with all remaining confidence
                return PreferredChoice(post_canon_candidates[0].value,
                                       candidate.sources, confidence)
            else:
                # Hmm.  Not in canonical form.
                #
                # XXX: It's not really clear what the best choice is here.
                # For now, if more than 3 sources agree on the non-canonical
                # form, use it.  Otherwise, return the canonical form.
                #
                # Subtract 30 confidence
                confidence -= 30
                threshold = 3
                if len(candidate.sources) >= threshold:
                    return PreferredChoice(candidate.value, candidate.sources,
                                           confidence)
                return PreferredChoice(cvalue, candidate.sources, confidence)

        if len(canonical_values) == 1:
            # All candidates are the same after canonicalization.
            (cvalue, sources) = canonical_values.iteritems().next()
            if cvalue in post_canon_candidates:
                # At least one candidate is in canonical form.
                # Use it, with almost all remaining confidence
                confidence -= 1
                return PreferredChoice(cvalue, sources, confidence)

            # Hmm.  No candidate is in canonical form.
            # For now, we just return the canonical value.
            #
            # We use a slightly higher confidence value than when they all
            # exactly agree but are non-canonical.
            #
            # TODO: If many candidates all agree on the same non-canonical
            # value, and only 1 or 2 disagree, maybe we should use the value
            # chosen by the majority?  (However, in most cases we only have 2
            # or 3 sources, so this shouldn't be a big deal in practice.)
            confidence -= 25
            return PreferredChoice(cvalue, sources, confidence)

        # Doh.  Not all candidates agree after canonicalization.
        #
        # Pick the one with the highest score.
        best_candidate = None
        num_ties = 0
        confidence -= 50
        for candidate in post_canon_candidates:
            if best_candidate is None:
                best_candidate = candidate
            elif candidate.score > best_candidate.score:
                best_candidate = candidate
                num_ties = 0
            elif candidate.score == best_candidate.score:
                num_ties += 1

        if num_ties > 0:
            confidence /= num_ties
        return PreferredChoice(best_candidate.value, best_candidate.sources,
                               confidence)
