"""
A utility to syllabify Latin words stored in
Cantus Database. As a result, this utility assumes latin transcription
conventions of CantusDB (found in the "Text Entry and Editing" pdf
at https://cantus.uwaterloo.ca/documents) which include both standardized
classical latin spelling and non-standardized (ie. what is 
actually in the manuscript) spellings. Consult the README for more
details.

Use syllabify_word to syllabify a word.

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
_CONSONANT_GROUPS = ["ch", "ph", "th", "rh"] + [
    x[0] + x[1] for x in itertools.product("pbtdcfg", "lr")
]

_DIPTHONGS = [
    "ae",
    "au",
    "oe",
]
_VOWELS = [
    "a",
    "e",
    "i",
    "o",
    "u",
]

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


def _is_vowel(char: str) -> bool:
    """
    Checks if a character is a vowel.

    char [str]: character to check

    returns [bool]: True if char is a vowel, False otherwise
    """
    return char in _VOWELS


def _is_consonant_group(chars: str) -> bool:
    """
    Checks if a string is a consonant group.

    chars [str]: string to check

    returns [bool]: True if chars is a consonant group,
        False otherwise
    """
    return chars in _CONSONANT_GROUPS


def _get_vowel_group(word: str, word_indexer: int) -> str:
    """
    Gets the entire vowel group starting at specific index.

    word [str]: word to get vowel group from
    word_indexer [int]: index of first vowel in vowel group

    returns [str]: vowel group
    """
    # Start vowel group with identified vowel
    vowel_found = word[word_indexer]
    # If at the end of the word, return the vowel.
    if word_indexer == len(word) - 1:
        return vowel_found
    # If the following letter is not a vowel, return the single vowel.
    if not _is_vowel(word[word_indexer + 1]):
        return vowel_found
    # If following letter is a vowel, there are four possibilities:
    # 1. the two vowels are a dipthong
    # 2. the two vowels are a diaeresis
    # 3. the two vowels are part of a vowel + i + vowel construction,
    #    in which case the first vowel is the only vowel in the group and
    #    the i is a consonant.
    # 4. the two vowels are part of a qu + vowel construction, in which case
    #    the final vowel is the only vowel in the group and the qu is a
    #    consonant.
    if f"{vowel_found}{word[word_indexer + 1]}" in _DIPTHONGS:
        return word[word_indexer : word_indexer + 2]
    if _is_vowel(word[word_indexer - 1]) and vowel_found == "i":
        return word[word_indexer : word_indexer + 2]
    if word[word_indexer - 1] == "q" and vowel_found == "u":
        return word[word_indexer : word_indexer + 2]
    return vowel_found


def _get_vowel_group_positions(word: str) -> "list[tuple[int, int]]":
    """
    Gets the positions of the vowel groups in a word.

    word [str]: word to get vowel groups from

    returns [list[int]]: list of positions of vowel groups; positions are
        tuples of the form (start index, end index).
    """
    vowel_group_pos = []
    word_indexer = 0
    while word_indexer < len(word):
        if _is_vowel(word[word_indexer]):
            vowel_group = _get_vowel_group(word, word_indexer)
            vowel_group_pos.append((word_indexer, word_indexer + len(vowel_group)))
            word_indexer += len(vowel_group)
            continue
        word_indexer += 1
    return vowel_group_pos


def _get_syl_bound_position(ltrs_btw_vow_grps: str) -> tuple[int, str]:
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
        split_case = "Hiatus or i as consonant"
    elif ltrs_btw_vow_grps[0] == "x":
        syl_bound = 1
        split_case = "X is double consonant"
    elif num_ltrs_btw_vow_grps == 1:
        split_case = "1 consonant between vowels"
    elif num_ltrs_btw_vow_grps == 2:
        if not _is_consonant_group(ltrs_btw_vow_grps):
            syl_bound = 1
            split_case = "2 consonants between vowels"
        else:
            split_case = "2 consonants between vowels (consonant group)"
    else:
        if _is_consonant_group(ltrs_btw_vow_grps[:2]):
            syl_bound = 2
        else:
            syl_bound = 1
        split_case = "3+ consonants between vowels"
    return syl_bound, split_case


def _find_word_syl_bounds(word: str) -> "list[int]":
    """
    Finds indices of the syllable boundaries of a word.
    See README for details on syllabification rules.

    word [str]: word to syllabify

    returns [list[int]]: list of syllables
    """
    logging.debug("Finding syllables: %s", word)

    if len(word) <= 1:
        logging.debug("### Final word syllabification: %s", word)
        return None

    # Each syllable has one and only one vowel group, so
    # we start by finding the positions of those vowel groups.
    vowel_group_pos = _get_vowel_group_positions(word)
    if len(vowel_group_pos) == 1:
        logging.debug("### Final word syllabification: %s", word)
        return None
    # We start by assuming that the syllable boundaries of the word
    # are at the end of each vowel group (except the final group, which ends
    # at the end of the word). We then modify these boundaries
    # in cases where there is more than one consonant between two vowel groups.
    syllable_boundaries = [x[1] for x in vowel_group_pos[:-1]]
    logging.debug(
        "### Vowel group split: %s",
        "".join(split_word_by_syl_bounds(word, syllable_boundaries)),
    )
    # We iterate through successive pairs of vowel groups, and if there is more than one
    # letter between the two vowel groups, we determine how to move the syllable boundary.
    ed_syllable_boundaries = []
    for syl_bound, vg_pos_1, vg_pos_2 in zip(
        syllable_boundaries, vowel_group_pos[:-1], vowel_group_pos[1:]
    ):
        # Find the letters between the end of the first
        # vowel group and the start of the second vowel group.

        ltrs_btw_vow_grps = word[vg_pos_1[1] : vg_pos_2[0]]
        prev_syl_bound = syl_bound
        syl_bound_adj, split_case = _get_syl_bound_position(ltrs_btw_vow_grps)
        syl_bound += syl_bound_adj
        if prev_syl_bound == syl_bound:
            logging.debug(
                "### CASE: %s. No change: %s",
                split_case,
                f"{word[:syl_bound]}-{word[syl_bound:]}",
            )
        else:
            logging.debug(
                "### CASE: %s. %s --> %s",
                split_case,
                f"{word[:prev_syl_bound]}-{word[prev_syl_bound:]}",
                f"{word[:syl_bound]}-{word[syl_bound:]}",
            )
        ed_syllable_boundaries.append(syl_bound)
    logging.debug(
        "### Final word syllabification: %s",
        "".join(split_word_by_syl_bounds(word, ed_syllable_boundaries)),
    )
    return ed_syllable_boundaries


def syllabify_word(
    word: str, return_syllabified_string: bool = False
) -> Union["list[int]", str]:
    """
    See README for details on syllabification rules.

    word [str]: word to syllabify
    return_syllabified_string [bool]: see return value. Default is False.

    returns [list[int] or str]: By default, returns a list of integers representing
        the indices of the syllable boundaries of word. Indices indicate the letter that begins
        the syllable. For example, the word "podatus" would return [2, 4] (po-da-tus).
        If a one-syllable word is passed, returns an empty list. If return_syllabified_string
        is True, returns a string with hyphens inserted at the syllable boundaries.
    """
    if LATIN_ALPH_REGEX.search(word):
        raise ValueError(f"Word {word} contains non-alphabetic characters.")
    syllable_boundaries = _find_word_syl_bounds(word)
    if not return_syllabified_string:
        if syllable_boundaries:
            return syllable_boundaries
        return []
    return "".join(split_word_by_syl_bounds(word, syllable_boundaries))
