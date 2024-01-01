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


def preprocess_volpiano(raw_volpiano_str: str) -> Tuple[str, str]:
    """
    Prepares volpiano string for alignment with text:
    - Checks for any invalid characters
    - Ensure volpiano begins with a clef followed by three hyphens. Assume
        that anything entered before the first clef should be removed, and
        that any additional clefs are erroneous.
    - Ensures volpiano string has an ending barline ("3" or "4")

    raw_volpiano_str [str]: unprocessed volpiano string

    returns [Tuple[str, str]]: preprocessed volpiano string without
        beginning clef or final barline and the final barline
        of the volpiano string
    """
    # Remove existing clef and any material preceding the
    # clef.
    vol_clef_rmvd: str = STARTING_MATERIAL_REGEX.sub("", raw_volpiano_str)
    # Remove existing ending bar line and add a "clean" ending barline.
    last_char: str = vol_clef_rmvd[-1]
    if last_char not in "34":
        last_char = "3"
    vol_clef_fin_bar_rmvd = vol_clef_rmvd.rstrip("3").rstrip("4").rstrip("-") + "---"
    processed_vol = INVALID_VOLPIANO_CHARS_REGEX.sub("", vol_clef_fin_bar_rmvd)
    logging.debug("Preprocessed volpiano string: %s", processed_vol)
    return processed_vol, last_char


def syllabify_volpiano(volpiano: str) -> List[SyllabifiedVolpianoSection]:
    """
    Splits the volpiano string into sections, words, and syllables.

    volpiano [str]: volpiano string

    returns [List[SyllabifiedVolpianoSection]: An object of class
        SyllabifiedVolpianoSection containing the syllabified volpiano
        string. See syllabified_section.py for more information.
    """
    volpiano_sections: List[str] = VOLPIANO_SECTIONING_REGEX.split(volpiano)
    # Filter out empty sections created by the split
    volpiano_sections = list(filter(lambda x: x != "", volpiano_sections))
    syllabified_volpiano: List[SyllabifiedVolpianoSection] = []
    for vol_sec in volpiano_sections:
        # We don't syllabify barlines or missing music markers
        if vol_sec[0] in "346":
            syllabified_volpiano.append(SyllabifiedVolpianoSection([[vol_sec]]))
            continue
        vol_words = VOLPIANO_WORD_REGEX.findall(vol_sec)
        syllabified_words: List[List[str]] = []
        for vol_word in vol_words:
            vol_syls = VOLPIANO_SYLLABLE_REGEX.findall(vol_word)
            syllabified_words.append(vol_syls)
        syllabified_volpiano.append(SyllabifiedVolpianoSection(syllabified_words))
    logging.debug(
        "Syllabified volpiano: %s", ", ".join(str(s) for s in syllabified_volpiano)
    )
    return syllabified_volpiano


def ensure_end_of_word_spacing(volpiano: str) -> str:
    """
    Ensures that a string ends with three hyphens.

    volpiano [str]: volpiano string

    returns [str]: volpiano string ending with a syllable break
    """
    if volpiano[-3:] != "---":
        return volpiano.rstrip("-") + "---"
    return volpiano


def adjust_music_spacing(
    volpiano_syllable: str, text_length: int, end_of_word: bool
) -> str:
    """
    Adjust trailing hyphens in volpiano syllables to ensure there
    are no gaps in the rendered staff. Ensures that the volpiano
    syllable is at least as long as the text syllable and that
    final volpiano syllables end with three hyphens.

    text_syllable [str]: syllable of text
    volpiano_syllable [str]: syllable of volpiano

    returns [str]: volpiano syllable with spacing added if necessary
    """
    if text_length > len(volpiano_syllable):
        volpiano_syllable += "-" * (text_length - len(volpiano_syllable))
    if end_of_word:
        volpiano_syllable = ensure_end_of_word_spacing(volpiano_syllable)
    return volpiano_syllable


def adjust_missing_music_spacing(volpiano: str, text_length: int) -> str:
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