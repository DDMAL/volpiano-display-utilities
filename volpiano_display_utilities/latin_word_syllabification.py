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

import logging
import re
from typing import Union, Tuple, List, Set

# Consonant groups are groups of consonants that are treated as a single
# consonant for the purposes of syllabification. For details, see README.
_CONSONANT_GROUPS: Set[str] = {
    "ch",
    "ph",
    "th",
    "rh",
    "gn",
    "qu",
    "gu",
    "sc",
    "pl",
    "pr",
    "bl",
    "br",
    "tr",
    "dr",
    "cl",
    "cr",
    "fl",
    "fr",
    "gl",
    "gr",
    "st",
}


_NASALIZED_CONSONANTS: Set[str] = {"m", "n"}

# Prefix groups are groups of characters that serve as common prefixes. For details,
# see README.
_PREFIX_GROUPS: Set[str] = {"ab", "ob", "ad", "per", "sub", "in", "con", "co"}

_VOWELS: Set[str] = {"a", "e", "i", "o", "u", "y"}
_VOWELS_AEOU: Set[str] = {"a", "e", "o", "u"}
_VOWELS_AEIOU: Set[str] = {"a", "e", "i", "o", "u"}
_VOWELS_AEO: Set[str] = {"a", "e", "o"}
_VOWELS_EOU: Set[str] = {"e", "o", "u"}
_VOWELS_IY: Set[str] = {"i", "y"}
_VOWELS_IUY: Set[str] = {"i", "u", "y"}
_QG: Set[str] = {"q", "g"}

LATIN_ALPH_REGEX = re.compile(r"[^a-zA-Z]")


class LatinError(ValueError):
    """
    Raised when a non-alphabetic character is found in a Latin word.
    """


def split_word_by_syl_bounds(word: str, syl_bounds: List[int]) -> List[str]:
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
    Returns the prefix of a word, if it has one that is followed by a vowel.
    For details on prefixes, see README.

    word [str]: word to check for prefix

    returns [str]: the word prefix. If word has no prefix, returns
        empty string.
    """
    for prefix in _PREFIX_GROUPS:
        # If the word is itself one of the prefixes (eg. "in" can
        # be a word or a prefix), don't return a prefix
        if word.startswith(prefix) and (word != prefix):
            prefix_length = len(prefix)
            if word[prefix_length] in _VOWELS:
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
    try:
        if (first_let == "y") and (word[1] in _VOWELS_AEIOU):
            word_w_repl += "j"
        elif (first_let == "i") and (
            (word[1] in _VOWELS_AEOU) or (word[1] == "h" and word[2] in _VOWELS_AEO)
        ):
            word_w_repl += "j"
        elif (first_let == "u") and (word[1] in _VOWELS):
            word_w_repl += "v"
        else:
            word_w_repl += first_let
    except IndexError:
        # IndexError will only occur on "ih"
        return word
    word = word[1:]
    # Handle remaining characters
    while word != "":
        char = word[0]
        if char not in _VOWELS_IUY or len(word) == 1:
            word_w_repl += char
        elif char in _VOWELS_IY:
            if ((word_w_repl[-1] in _VOWELS_AEOU) and (word[1] in _VOWELS_AEOU)) or (
                (word_w_repl[-2:] not in _CONSONANT_GROUPS)
                and (word_w_repl[-1] == "h")
                and (word[1] in _VOWELS_EOU)
            ):
                word_w_repl += "j"
            else:
                word_w_repl += "i"
        elif char == "u":
            if word_w_repl[-1] in _QG and word[1] in _VOWELS:
                word_w_repl += "w"
            elif word_w_repl[-1] in _VOWELS and word[1] in _VOWELS:
                word_w_repl += "v"
            else:
                word_w_repl += "u"
        word = word[1:]
    return word_w_repl


def _get_vowel_positions(word: str) -> List[int]:
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
    # Replace semi-vowels for the purposes of finding vowels.
    word = _replace_semivowels_and_v(word)
    logging.debug("Semivowels, long i's, v's found: %s", word)
    vowel_positions = [idx for idx, char in enumerate(word) if char in _VOWELS]
    return vowel_positions


def _get_syl_bound_position(ltrs_btw_vow_grps: str) -> Tuple[int, str]:
    """
    Find the adjustment required to a syllable boundary between
    two vowel groups based on the letters between them.

    We handle 4 general cases.

    1. No consonants between vowel groups: keep the syllable boundary
          where it is diaeresis unless we have vowel + i + vowel,
          in which case we split as [vowel] + [i + vowel]
    2. 1 consonant between vowel groups: keep the syllable boundary
          where it is (consonant is part of second syllable)
    3. 2 consonants between vowel groups: split the first consonant to the
          first syllable, unless the two consonants form a consonant group, in
          which case keep the group on the second syllable.
    4. 3+ consonants between vowel groups: group the final two consonants of
          a 3-consonant sequence between vowel groups, if possible, and place preceding
          consonants in the preceding syllable. If these cannot be grouped or there
          are more than three consonants between vowel groups, group the
          first two consonants, if possible, and add following consonants to the
          following syllable. If neither the final two nor first two consonants can
          be grouped, split the syllable after the first consonant.

    EXCEPTION: If the first consonant of a sequence of 2 or more consonants between
    vowels is a nasalized consonant ("m" or "n"), we don't treat it as a consonant
    for the purposes of the cases above. In practice, this means we only need to check
    for the existence of a nasalized consonant at the start of a sequence of 3 or more
    consonants between vowels (in the two consonant case, an initial "m" or "n" in the
    sequence is already added to the preceding syllable).

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
    num_ltrs_btw_vow_grps: int = len(ltrs_btw_vow_grps)
    # Default case: syllable boundary immediately follows previous
    # vowel group.
    if num_ltrs_btw_vow_grps == 0:
        return 0, "Hiatus"
    if ltrs_btw_vow_grps[0] == "x":
        return 1, "X is double consonant"
    if num_ltrs_btw_vow_grps == 1:
        return 0, "1 consonant between vowels"
    # If the first letter of the consonant sequence is a nasalized consonant,
    # we add it to the prior syllable and treat the remaining consonants
    # as if they were the only consonants between the vowel groups.
    num_consonants: int = num_ltrs_btw_vow_grps
    if ltrs_btw_vow_grps[0] in _NASALIZED_CONSONANTS:
        syl_bound: int = 1
        ltrs_btw_vow_grps = ltrs_btw_vow_grps[1:]
        num_ltrs_btw_vow_grps -= 1
        # If there is only one consonant remaining, we treat it as the only
        # consonant between the vowel groups and add it to the following syllable.
        if num_ltrs_btw_vow_grps == 1:
            return syl_bound, "2 consonants between vowels"
    else:
        syl_bound = 0
    if num_ltrs_btw_vow_grps == 2:
        if ltrs_btw_vow_grps not in _CONSONANT_GROUPS:
            syl_bound += 1
            split_case: str = f"{num_consonants} consonants between vowels"
        else:
            split_case = f"{num_consonants} consonants (consonant group) between vowels"
    elif ltrs_btw_vow_grps == "str":
        split_case = f"{num_consonants} consonants ('str' group) between vowels"
    elif ltrs_btw_vow_grps[1:] in _CONSONANT_GROUPS:
        syl_bound += 1
        split_case = f"{num_consonants} consonants (consonant group) between vowels"
    elif ltrs_btw_vow_grps[:2] in _CONSONANT_GROUPS:
        split_case = f"{num_consonants} consonants (consonant group) between vowels"
    else:
        syl_bound += 1
        split_case = f"{num_consonants} consonants between vowels"
    return syl_bound, split_case


def _syllabify(word: str) -> List[int]:
    """
    Finds indices of the syllable boundaries of a word.
    See README for details on syllabification rules.

    word [str]: word to syllabify

    returns [list[int]]: list of indices indicating where
        in word syllables begin
    """
    logging.debug("Finding syllables: %s", word)

    syllable_boundaries: List[int] = []

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


def syllabify_word(word: str, return_string: bool = False) -> Union[List[int], str]:
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
        raise LatinError(f"Word {word} contains non-alphabetic characters.")
    lowercase_word = word.lower()
    syllable_boundaries = _syllabify(lowercase_word)
    if return_string:
        return "".join(split_word_by_syl_bounds(word, syllable_boundaries))
    return syllable_boundaries
