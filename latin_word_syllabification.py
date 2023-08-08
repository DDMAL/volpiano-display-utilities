"""
Module provides a function, syllabify_word, that syllabifies a Latin word. Although
this function does not assume any specific spelling convention, it was 
developed for use syllabifying texts (with both standard and non-standard spellings)
entered in Cantus Database. As such, familiarity with the conventions of Cantus
Database may be helpful; details can be found in the "Text Entry and Editing" pdf
at https://www.cantusdatabase.org/documents). Consult the README for more
details about the syllabification logic implemented in this function.

syllabify_word(word, return_syllabified_string = False) 
    word [str]: string to syllabify
    return_syllabified_string [bool]: if True, returns a string with
        syllables separated by hyphens; if False, returns a list of
        indices of syllable boundaries. Defaults to False.

returns a list of syllables with syllable boundaries marked by hyphens.

The function split_word_by_syl_bounds can be used to split a word
into syllables based on syllable boundaries. See function docstring
for more details.

Logs at level = DEBUG.
"""

import itertools
import logging
import re
from typing import Union

# Consonant groups are groups of consonants that are treated as a single
# consonant for the purposes of syllabification. For details, see README.
_CONSONANT_GROUPS = ["ch", "ph", "th", "rh", "gn", "qu", "gu", "nc", "mp", "sc"] + [
    x[0] + x[1] for x in itertools.product("pbtdcfg", "lr")
]

# Prefix groups are groups of characters that serve as common prefixes. For details,
# see README.
_PREFIX_GROUPS = ["ab", "ob", "ad", "per", "sub", "in", "con"]

LATIN_ALPH_REGEX = re.compile(r"[^a-zA-Z]")


def split_word_by_syl_bounds(word: str, syl_bounds: "list[int]") -> "list[str]":
    """
    Splits a word into syllables based on syllable boundaries.

    word [str]: word to split
    syl_bounds [list[int]]: list of syllable boundaries. If a one-syllable
        word, should be [].

    returns [list[str]]: list of syllables, with hyphens added at the
        end of non-final syllables
    """
    if len(syl_bounds) == 0:
        return [word]
    # Start with the first syllable (characters before first boundary)
    syllables = [f"{word[:syl_bounds[0]]}-"]
    # Add middle syllables (characters between boundaries)
    for bnd1, bnd2 in zip(syl_bounds[:-1], syl_bounds[1:]):
        syllables.append(f"{word[bnd1:bnd2]}-")
    # Finish with last syllable (characters after last boundary)
    syllables.append(word[syl_bounds[-1] :])
    return syllables


def _get_prefixes(word: str) -> str:
    """
    Returns the profix of a word, if it has one.

    word [str]: word to check for prefix

    returns [str]: the word prefix. If word has no prefix, returns
        empty string.
    """
    for prefix in _PREFIX_GROUPS:
        # If the word is itself one of the prefixes (eg. "in" can
        # be a word or a prefix), doen't return a prefix
        if word.startswith(prefix) and (word != prefix):
            return prefix
    return ""


def _replace_semivowels_and_v(word: str) -> str:
    """
    Replaces the characters "u", "i", and "y" with other characters
    if they serve as consonants or semivowels. This allows the syllabification
    algorithm to skip them when finding vowels. For details on semivowels
    and "u"/"v", see README.

    Where "i" or "y" are serving as semivowels, they are replaced with "j".
    Where "u" is serving as a semivowel, it is replaced with "w".
    Where "u" is serving as a consonant, it is replaced with "v".

    word [str]: word to replace characters in

    returns [str]: word with characters replaced
    """
    word_w_repl = ""
    # Handle first character in the word
    first_let = word[0]
    if (first_let in "y") and (word[1] in "aeiouyh"):
        word_w_repl += "j"
    elif (first_let == "i") and (word[1] in "aeouyh"):
        word_w_repl += "j"
    elif (first_let == "u") and (word[1] in "aeiouy"):
        word_w_repl += "v"
    else:
        word_w_repl += first_let
    word = word[1:]
    # Handle remaining characters
    while word != "":
        char = word[0]
        if char not in "iyu" or len(word) == 1:
            word_w_repl += char
        elif char in "iy":
            if ((word_w_repl[-1] in "aeu") and (word[1] in "aeu")) or (
                (word_w_repl[-2:] not in _CONSONANT_GROUPS)
                and (word_w_repl[-1] == "h")
                and (word[1] in "aeiouy")
            ):
                word_w_repl += "j"
            else:
                word_w_repl += "i"
        elif char == "u":
            if word_w_repl[-1] in "qg" and word[1] in "aeiouy":
                word_w_repl += "w"
            elif word_w_repl[-1] in "aeiouy" and word[1] in "aeiouy":
                word_w_repl += "v"
            else:
                word_w_repl += "u"
        word = word[1:]
    return word_w_repl


def _get_vowel_positions(word: str) -> "list[int]":
    """
    Gets the positions of vowels in a word.

    Vowels are "a", "e", "i", "o", "u", "y" and long "i" (written "j"),
    except in such cases where "i"/"j" and "u" are semi-vowels or the written
    "u" is pronounced "v." We temporarily replace these characters in those cases
    with other consonants when finding vowel positions.

    word [str]: word to get vowel groups from

    returns [list[int]]: list of string indices of vowels in word
    """
    # Replace long "i" ("j") with "i" for the purposes of finding vowels.
    # Note: places where a semi-vowel was transcribed "j" will be handled
    # by the _replace_semivowels function.
    word = word.replace("j", "i")
    # Replace semi-vowelsn for the purposes of finding vowels.
    word = _replace_semivowels_and_v(word)
    logging.debug("Semivowels, long i's, v's found: %s", word)
    vowel_positions = []
    word_indexer = 0
    while word_indexer < len(word):
        char = word[word_indexer]
        if char in "aeiouy":
            vowel_positions.append(word_indexer)
            word_indexer += 1
        else:
            word_indexer += 1
    return vowel_positions


def _get_syl_bound_position(ltrs_btw_vow_grps: str) -> "tuple[int, str]":
    """
    Find the adjustment required to a syllable boundary between
    two vowel groups based on the letters between them.

    We handle 4 general cases.

    1. No consonants between vowel groups: keep the syllable boundary
          where it is diaeresis unless we have vowel + i + vowel,
          in which case we split as [vowel] + [i + vowel]
    2. 1 consonant between vowel groups: keep the syllable boundary
          where it is (consonant is part of second syllable)
    3. 2 consonants between vowel groups: split the first consonant to  the
          first syllable, unless the two consonants form a consonant group, in
          which case keep the group on the second syllable
    4. 3+ consonants between vowel groups: add the first consonant or
          consonant group to the first syllable

    Two additional special cases exist. "X" is treated as a double consonant
    "ks" and the letter terminates the previous syllable. In cases where "i"
    is between two vowels, but not part of a dipthong, it is treated as a
    consonant and begins the following syllable.

    ltrs_btw_vow_grps [str]: letters between two vowel groups

    returns [tuple[int, str]]: tuple of the form (syl_bound, split_case),
        where syl_bound is the index of the syllable boundary relative to the
        start of ltrs_btw_vow_grps (eg. 0 = syllable boundary before
        first letter, 1 = syllable boundary between first and second letters, etc.)
        and split_case is a string describing the case used to determine the
        syllable boundary (passed to logger).
    """
    num_ltrs_btw_vow_grps = len(ltrs_btw_vow_grps)
    # Default case: syllable boundary immediately follows previous
    # vowel group.
    syl_bound = 0
    if num_ltrs_btw_vow_grps == 0:
        split_case = "Hiatus"
    elif ltrs_btw_vow_grps[0] == "x":
        syl_bound = 1
        split_case = "X is double consonant"
    elif num_ltrs_btw_vow_grps == 1:
        split_case = "1 consonant between vowels"
    elif num_ltrs_btw_vow_grps == 2:
        if ltrs_btw_vow_grps not in _CONSONANT_GROUPS:
            syl_bound = 1
            split_case = "2 consonants between vowels"
        else:
            split_case = "2 consonants between vowels (consonant group)"
    else:
        if ltrs_btw_vow_grps[:2] in _CONSONANT_GROUPS:
            syl_bound = 2
        else:
            syl_bound = 1
        split_case = "3+ consonants between vowels"
    return syl_bound, split_case


def _syllabify(word: str) -> "list[int]":
    """
    Finds indices of the syllable boundaries of a word.
    See README for details on syllabification rules.

    word [str]: word to syllabify

    returns [list[int]]: list of syllables
    """
    logging.debug("Finding syllables: %s", word)

    syllable_boundaries = []

    if len(word) <= 1:
        logging.debug("### Final word syllabification: %s", word)
        return syllable_boundaries

    word_prefix = _get_prefixes(word)
    word_prefix_length = len(word_prefix)
    if word_prefix:
        syllable_boundaries.append(word_prefix_length)
        word_stem = word[len(word_prefix) :]
        word_prefix += "-"
        logging.debug("### Word prefix: %s", word_prefix)
    else:
        word_stem = word
    # Each syllable has one and only one vowel (either a
    # single vowel or a dipthong), so we start by finding
    # the positions of vowels. We will combine dipthongs later.
    vow_pos = _get_vowel_positions(word_stem)
    if len(vow_pos) == 1:
        logging.debug("### Final word syllabification: %s%s", word_prefix, word_stem)
        return syllable_boundaries
    # We start by assuming that the syllable boundaries of the word
    # are at the end of each vowel group (except the final group, which ends
    # at the end of the word). We then modify these boundaries
    # in cases where there is more than one consonant between two vowel groups.
    init_syllable_boundaries = [x + 1 for x in vow_pos[:-1]]
    logging.debug(
        "### Word stem vowel group split: %s",
        "".join(split_word_by_syl_bounds(word_stem, init_syllable_boundaries)),
    )
    # We iterate through successive pairs of vowel groups, and if there is more than one
    # letter between the two vowel groups, we determine how to move the syllable boundary.
    for syl_bound, v_pos_1, v_pos_2 in zip(
        init_syllable_boundaries, vow_pos[:-1], vow_pos[1:]
    ):
        prev_syl_bound = syl_bound
        # If two vowels are adjacent, check for a dipthong.
        if v_pos_2 - 1 == v_pos_1:
            dipthong = word_stem[v_pos_1 : v_pos_2 + 1]
            if dipthong in ["ae", "oe", "au"]:
                syl_bound += 1
                logging.debug(
                    "### CASE: Dipthong. %s --> %s",
                    f"{word_stem[:prev_syl_bound]}-{word_stem[prev_syl_bound:]}",
                    f"{word_stem[:syl_bound]}-{word_stem[syl_bound:]}",
                )
                continue
        ltrs_btw_vow_grps = word_stem[v_pos_1 + 1 : v_pos_2]
        syl_bound_adj, split_case = _get_syl_bound_position(ltrs_btw_vow_grps)
        syl_bound += syl_bound_adj
        if prev_syl_bound == syl_bound:
            logging.debug(
                "### CASE: %s. No change: %s",
                split_case,
                f"{word_stem[:syl_bound]}-{word_stem[syl_bound:]}",
            )
        else:
            logging.debug(
                "### CASE: %s. %s --> %s",
                split_case,
                f"{word_stem[:prev_syl_bound]}-{word_stem[prev_syl_bound:]}",
                f"{word_stem[:syl_bound]}-{word_stem[syl_bound:]}",
            )
        syllable_boundaries.append(syl_bound + word_prefix_length)
    logging.debug(
        "### Final word syllabification: %s",
        "".join(split_word_by_syl_bounds(word, syllable_boundaries)),
    )
    return syllable_boundaries


def syllabify_word(word: str, return_string: bool = False) -> Union["list[int]", str]:
    """
    See README for details on syllabification rules.

    word [str]: word (containing only latin alphabetic characters) to syllabify
    return_string [bool]: see return value. Default is False.

    returns [list[int] or str]: By default, returns a list of integers representing
        the indices of the syllable boundaries of word. Indices indicate the letter that begins
        the syllable. For example, the word "podatus" would return [2, 4] (po-da-tus).
        If a one-syllable word is passed, returns an empty list. If return_string
        is True, returns a string with hyphens inserted at the syllable boundaries.
    """
    if not isinstance(word, str):
        raise TypeError(f"Word must be a string. Got {type(word)}.")
    if LATIN_ALPH_REGEX.search(word):
        raise ValueError(f"Word {word} contains non-alphabetic characters.")
    lowercase_word = word.lower()
    syllable_boundaries = _syllabify(lowercase_word)
    if return_string:
        return "".join(split_word_by_syl_bounds(word, syllable_boundaries))
    return syllable_boundaries
