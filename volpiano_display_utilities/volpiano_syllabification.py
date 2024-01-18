"""
Functions for syllabifying volpiano strings into sections, words, and syllables.
"""

import re
from typing import List, Tuple
import logging

from .syllabified_section import SyllabifiedVolpianoSection

# A string containing all valid volpiano characters in Cantus
# Database. Used to check for invalid characters. Note that
# the "1" character (a clef) is not included here, as it is
# only valid at the start of a string, and is handled separately in
# the _preprocess_volpiano function.
INVALID_VOLPIANO_CHARS_REGEX = re.compile(
    r"[^\-9abcdefghijklmnopqrsyz)ABCDEFGHIJKLMNOPQRSYZ3467]"
)

# Matches any material before the first clef, the clef itself, and
# any following spacing in a volpiano string.
STARTING_MATERIAL_REGEX = re.compile(r"^.*?1-*")

# Split sections of volpiano on clefs, barline markers, and missing
# music indicators. Includes spacing (hyphens) and section markers (7's)
# in the split, if present.
VOLPIANO_SECTIONING_REGEX = re.compile(r"([34][\-7]*|6[\-7]*6[\-7]*)")

# Split words on sequences of three hyphens or at the end of the string.
VOLPIANO_WORD_REGEX = re.compile(r".*?-{3,}|.+$")

# Split syllables on sequences of two hyphens or at the end of the string.
VOLPIANO_SYLLABLE_REGEX = re.compile(r".*?-{2,}|.+$")


def prepare_volpiano_for_syllabification(raw_volpiano_str: str) -> Tuple[str, bool]:
    """
    Prepare volpiano string for syllabification:
    - Remove any invalid characters
    - Remove the opening clef and anything that appears before the
        opening clef

    raw_volpiano_str [str]: unprocessed volpiano string

    returns [str, bool]: preprocessed volpiano string without
        beginning clef and invalid characters and boolean indicating
        whether invalid volpiano characters or character preceding
        clef were removed
    """
    # Remove existing clef and any material preceding the
    # clef.
    vol_chars_rmvd_flag = False
    # Check whether the volpiano string clef was correctly encoded before
    # removing it.
    if raw_volpiano_str[0:4] != "1---" or raw_volpiano_str[0:5] == "1----":
        vol_chars_rmvd_flag = True
    vol_clef_rmvd = STARTING_MATERIAL_REGEX.sub("", raw_volpiano_str)
    processed_vol, num_substitutions = INVALID_VOLPIANO_CHARS_REGEX.subn(
        "", vol_clef_rmvd
    )
    # Check whether any invalid characters were removed from the volpiano
    if num_substitutions > 0:
        vol_chars_rmvd_flag = True
    logging.debug("Preprocessed volpiano string: %s", processed_vol)
    return processed_vol, vol_chars_rmvd_flag


def syllabify_volpiano(volpiano: str) -> Tuple[List[SyllabifiedVolpianoSection], bool]:
    """
    Split the volpiano string into sections, words, and syllables.

    volpiano [str]: volpiano string

    returns [List[SyllabifiedVolpianoSection, bool]: A list of SyllabifiedVolpianoSection
        objects containing the syllabified volpiano string and a boolean flagging whether
        the volpiano was improperly spaced.
        See syllabified_section.py for more information.
    """
    volpiano_improperly_spaced = False
    volpiano_sections: List[str] = VOLPIANO_SECTIONING_REGEX.split(volpiano)
    # Filter out empty sections created by the split
    volpiano_sections = list(filter(lambda x: x != "", volpiano_sections))
    syllabified_volpiano: List[SyllabifiedVolpianoSection] = []
    for vol_sec_idx, vol_sec in enumerate(volpiano_sections):
        # We don't syllabify barlines or missing music markers, but we
        # do check whether they are encoded with the appropriate spacing.
        if vol_sec[0] in "346":
            # Check if missing music sections are encoded as
            # "6------6---", with any break markers (7's) entered
            # immediate following the second "6".
            if vol_sec[0] == "6" and (
                vol_sec[-3:] != "---"
                or vol_sec[1:8] != "------6"
                or len(vol_sec.replace("7", "")) != 11
            ):
                volpiano_improperly_spaced = True
            # Check if barlines are encoded as "3---" or "4---",
            # with any break markers (7's) entered immediately
            # following the "3" or "4".
            elif (
                vol_sec[0] in "34"
                and vol_sec_idx != len(vol_sec) - 1
                and (vol_sec[-3:] != "---" or len(vol_sec.replace("7", "")) != 4)
            ):
                volpiano_improperly_spaced = True
            syllabified_volpiano.append(SyllabifiedVolpianoSection([[vol_sec]]))
            continue
        vol_words = VOLPIANO_WORD_REGEX.findall(vol_sec)
        syllabified_words: List[List[str]] = []
        for vol_word in vol_words:
            vol_syls = VOLPIANO_SYLLABLE_REGEX.findall(vol_word)
            # Check if the last syllable of the word is improperly spaced
            # with three and only three trailing hyphens.
            try:
                final_syl_of_word = vol_syls[-1]
                if final_syl_of_word[-3:] != "---" or final_syl_of_word[-4] == "-":
                    volpiano_improperly_spaced = True
            except IndexError:
                volpiano_improperly_spaced = True
            syllabified_words.append(vol_syls)
        syllabified_volpiano.append(SyllabifiedVolpianoSection(syllabified_words))
    logging.debug(
        "Syllabified volpiano: %s", ", ".join(str(s) for s in syllabified_volpiano)
    )
    return syllabified_volpiano, volpiano_improperly_spaced


def ensure_end_of_word_spacing(volpiano: str) -> str:
    """
    Ensure that a volpiano "word" ends with three hyphens.

    volpiano [str]: volpiano string

    returns [str]: volpiano string ending with three hyphens
    """
    if volpiano[-3:] != "---":
        return volpiano.rstrip("-") + "---"
    return volpiano


def adjust_volpiano_spacing_for_rendering(
    volpiano_syllable: str, text_length: int, end_of_word: bool
) -> str:
    """
    Adjust trailing hyphens in volpiano syllables to ensure there
    are no gaps in the rendered staff. Ensures that the volpiano
    syllable is at least as long as the text syllable and that
    final volpiano syllables end with three hyphens.

    volpiano_syllable [str]: syllable of volpiano
    text_length [int]: length of associated text syllable
    end_of_word [bool]: whether volpiano_syllable is at the end
        of a word

    returns [str]: volpiano syllable with spacing added if necessary
    """
    if text_length > len(volpiano_syllable):
        volpiano_syllable += "-" * (text_length - len(volpiano_syllable))
    if end_of_word:
        volpiano_syllable = ensure_end_of_word_spacing(volpiano_syllable)
    return volpiano_syllable


def adjust_missing_music_spacing_for_rendering(volpiano: str, text_length: int) -> str:
    """
    Adjusts the spacing of a section of missing music to match
    the length of the accompanying text, while preserving any
    breaks encoded in the volpiano string.

    volpiano [str]: volpiano string
    text_length [int]: length of text to be aligned with missing music

    returns [str]: volpiano string encoding missing music of
        the given length
    """
    if volpiano[0] != "6":
        raise ValueError("Not a missing music section")
    section_term = volpiano.split("6")[-1]
    if text_length <= 10:
        spaced_vol = "6------6"
    else:
        spaced_vol = "6" + "-" * text_length + "6"
    return ensure_end_of_word_spacing(spaced_vol + section_term)
