#!/usr/bin/python -tt
#
# Copyright (c) 2009, Adam Simpkins
#
import collections
import re

SCORE_WARN = 50
SCORE_GOOD = 90


class FieldTypeError(TypeError):
    def __init__(self, field, value, msg):
        TypeError.__init__(self, 'invalid value type %r for %r field: %s' %
                           (value, field.__name__, msg))
        self.field = field
        self.value = value
        self.message = msg


class FieldValueError(ValueError):
    def __init__(self, field, value, msg):
        ValueError.__init__(self, 'invalid value %r for %r field: %s' %
                            (value, field.__name__, msg))
        self.field = field
        self.value = value
        self.message = msg


class Field(object):
    """
    A metadata field
    """
    def __init__(self, name, sort_key):
        self.name = name
        # The sortKey is used for specifying the order that should normally
        # be used when displaying fields.
        self.sortKey = 0
        self.value = None

        # The candidates is set to a merge.candidates.CandidatesList object
        # when merging metadata information from multiple sources.
        self.candidates = None

    def set(self, value):
        value = self.coerce(value)
        self.validate(value)
        self.value = value

    @staticmethod
    def canonicalize(value):
        return value

    @staticmethod
    def squash(value):
        return value

    @staticmethod
    def coerce(value):
        return value

    @staticmethod
    def validate(value):
        pass

    @staticmethod
    def computeScore(value):
        return SCORE_GOOD

    def __str__(self):
        return unicode(self.value).encode('utf-8')

    def __unicode__(self):
        return unicode(self.value)

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self.value)


class StringField(Field):
    @classmethod
    def coerce(clazz, value):
        if not isinstance(value, unicode):
            raise FieldTypeError(clazz, value, 'must be a unicode string')
        return value

    @staticmethod
    def squash(value):
        # Remove all punctuation characters
        symbols_pattern = '[~!@#$%^&*()\\-_+={}[\\]|\\\\/<>,.?:;\'"]'
        value = re.sub(symbols_pattern, '', value)

        # Replace all contiguous whitespace with a single space
        value = re.sub('\s\+', ' ', value)
        return value


class IntField(Field):
    @classmethod
    def coerce(clazz, value):
        if isinstance(value, (unicode, str)):
            try:
                return int(value)
            except ValueError:
                raise FieldValueError(clazz, value,
                                      'value does not represent an integer')
        if isinstance(value, (int, long)):
            return value

        raise FieldValueError(clazz, value, 'expected an integer')


class StringListField(Field):
    @classmethod
    def coerce(clazz, value):
        if isinstance(value, unicode):
            return [value]

        if isinstance(value, collections.Container):
            for elem in value:
                if not isinstance(elem, unicode):
                    raise FieldTypeError(clazz, value,
                                         'must contain only unicode strings')
            return list(value)

        raise FieldTypeError(clazz, value,
                             'expected a list of unicode strings')


# TODO: In the future, we should have configurable scoring/canonicalization
# mechanisms, for users who prefer other styles.
class TitleField(StringField):
    @staticmethod
    def canonicalize(value):
        # Capitalize the beginning of each word.
        # Don't use string.capwords(), since that also lowercases
        # all characters but the first.
        new_chars = []
        at_word_start = True
        for c in value:
            if c.isspace():
                at_word_start = True
                new_chars.append(c)
            else:
                if at_word_start:
                    new_chars.append(c.upper())
                else:
                    new_chars.append(c)
                at_word_start = False

        return ''.join(new_chars)

    @staticmethod
    def computeScore(value):
        # Examine the string to check for some things we care about
        num_symbols = 0
        is_all_caps = True
        is_title_case = True
        has_multi_character_tokens = False

        symbols = '~!@#$%^&*()-_+={}[]|\\/<>,.?:;\'"'
        at_word_start = True
        prev_is_alpha = False
        for c in value:
            if c.isalpha():
                # Any lowercase character means is_all_caps is false
                if c.islower():
                    is_all_caps = False

                # If we are at the start of a word, and the current
                # character is not uppercase, some of the words aren't title
                # cased.
                if at_word_start and not c.isupper():
                    is_title_case = False

                # If the previous character was also an alpha char,
                # the string contains some multi-character tokens
                #
                # (We don't use at_word_start here, since "A.B.C"
                # is treated as a single word.)
                if prev_is_alpha:
                    has_multi_character_tokens = True

                # For the next character after an alpha character,
                # we're no longer at the start of a word, and the previous
                # character was alpha
                at_word_start = False
                prev_is_alpha = True
            else:
                # Whitespace ends the current word.
                # The next alpha character is the start of the next word.
                #
                # We don't treat punctuation as ending the current word.
                # This is most important for single quote ('), as it appears
                # in contractions ("don't") and possessives ("Bob's").
                if c.isspace():
                    at_word_start = True
                if c in symbols:
                    num_symbols += 1
                prev_is_alpha = False

        if is_all_caps and has_multi_character_tokens:
            # Some CDDB entries are in all caps.
            # Give a very low score for this.
            #
            # However, don't penalize strings that only have single character
            # tokens.  (This handles values that are just acronyms, or just a
            # single letter. e.g. - "B.B.K", "U.N.C.L.E.", "X")
            score = SCORE_WARN - 30
        elif not is_title_case:
            # I prefer consistently capitalizing the first letter of each
            # word in almost all cases.  (Even for words like "the" and
            # "of").  Mark this as a warning, and give a smaller than normal
            # score.
            score = SCORE_WARN
        else:
            # Great.  Title-case, but not all caps.
            score = SCORE_GOOD

        # Give a small bonus for symbols and punctuation.
        # (Some people and tools strip out these characters.  A value with
        # punctuation symbols is therefore more likely to be accurate.)
        #
        # Don't count more than 5 symbols, though.  (We don't want to prefer
        # garbage entries containing all symbols.)
        symbol_bonus = num_symbols
        if symbol_bonus > 5:
            suymbol_bonus = 5
        score += symbol_bonus

        return score
