"""
Module that aligns the syllabified text and melody (encoded in volpiano) of a chant. This
module assumes that text and melody have been entered according to the conventions of Cantus
Database (more details about these conventions can be found 
at https://cantusdatabase.org/documents). See the README for more information.

Use align_text_and_volpiano to align the text and melody strings of a chant.
"""
import re
import logging
from itertools import zip_longest
from typing import List, Tuple
from .cantus_text_syllabification import syllabify_text

# A string containing all valid volpiano characters in Cantus
# Database. Used to check for invalid characters.
INVALID_VOLPIANO_CHARS_REGEX = re.compile(
    r"[^\-19abcdefghijklmnopqrsyz)ABCDEFGHIJKLMNOPQRSYZ3467]"
)

# Matches any material before the clef, the clef itself, and
# any following spacing in a volpiano string.
STARTING_MATERIAL_REGEX = re.compile(r".*1-*")

# Split sections of volpiano on clefs, barline markers, and missing
# music indicators. Includes spacing (hyphens) and section markers (7's)
# in the split, if present.
VOLPIANO_SECTIONING_REGEX = re.compile(r"([134][\-7]*|6[\-7]*6[\-7]*)")

VOLPIANO_WORD_REGEX = re.compile(r".*?---")

VOLPIANO_SYLLABLE_REGEX = re.compile(r".*?-{2,3}")


def _preprocess_volpiano(raw_volpiano_str: str) -> str:
    """
    Prepares volpiano string for alignment with text:
    - Checks for any invalid characters
    - Ensure volpiano begins with a clef followed by three hyphens. Assume
        that anything entered before a clef should be removed.
    - Ensures proper spacing around barlines ("3" and "4") and missing
        music indicators ("6")
    - Ensures volpiano string has an ending barline ("3" or "4")
    - Finds line and page breaks and removes them from the volpiano string
        (they are added back in postprocessing)

    raw_volpiano_str [str]: unprocessed volpiano string

    returns [str]: preprocessed volpiano string
    """
    # Remove existing clef and any material preceding the
    # clef. Re-add a "clean" starting clef.
    vol_clef_rmvd = STARTING_MATERIAL_REGEX.sub("", raw_volpiano_str)
    vol_clef_added = "1---" + vol_clef_rmvd
    # Remove existing ending bar line and add a "clean" ending barline.
    last_char = vol_clef_added[-1]
    if last_char not in "34":
        last_char = "3"
    vol_clef_fin_bar_added = (
        vol_clef_added.rstrip("3").rstrip("4").rstrip("-") + "---" + last_char
    )
    processed_vol = INVALID_VOLPIANO_CHARS_REGEX.sub("", vol_clef_fin_bar_added)
    logging.debug("Preprocessed volpiano string: %s", processed_vol)
    return processed_vol


def _postprocess_spacing(
    comb_text_and_vol: List[Tuple[str, str]],
) -> List[Tuple[str, str]]:
    """
    Handle some special spacing requirements for optimal display
    of volpiano with chant text.

    Ensures that:
     - the length of missing music sections responds to the length of
        the text associated with the section
     - internal barlines have appropriate spacing

    comb_text_and_vol [list[tuple[str, str]]]:
        list of tuples of text syllables and volpiano syllables

    returns [list[tuple[str, str]]]: list of tuples of text syllables and
        volpiano syllables with spacing of missing music sections responsive
        to associated text length
    """
    comb_text_and_vol_rev_spacing = []
    # Spacing for the opening clef and final barline of the
    # volpiano string are handled in the preprocessing function
    # so we don't need to deal with those here.
    beg_clef_section = comb_text_and_vol[0]
    fin_bar_section = comb_text_and_vol[-1]
    comb_text_and_vol_rev_spacing.append(beg_clef_section)
    for text_elem, vol_elem in comb_text_and_vol[1:-1]:
        if vol_elem[0] == "6":
            text_length = len(text_elem)
            if text_length <= 10:
                vol_elem_spaced = "6------6"
            if text_length > 10:
                vol_elem_spaced = "6" + "-" * text_length + "6"
            vol_elem = vol_elem_spaced + vol_elem.split("6")[-1]
        elif vol_elem[0] in "34":
            num_hyphens = vol_elem.count("-")
            vol_elem += "-" * (3 - num_hyphens)
        comb_text_and_vol_rev_spacing.append((text_elem, vol_elem))
    comb_text_and_vol_rev_spacing.append(fin_bar_section)
    return comb_text_and_vol_rev_spacing


def _align_word(text_syls: List[str], volpiano_word: str) -> List[Tuple[str, str]]:
    """
    Align a word of text and volpiano, padding in case
    either text or volpiano is longer or shorter for that word.

    text_syls [list[str]]: list of syllables in the word
    volpiano_word [str]: volpiano string for the word

    returns [list[tuple[str, str]]]: list of tuples of text syllables and
        volpiano syllables aligned together
    """
    vol_syls = VOLPIANO_SYLLABLE_REGEX.findall(volpiano_word)
    # Squash final syllables of a word together if there are more
    # syllables in the text than in the volpiano.
    if len(text_syls) > len(vol_syls):
        txt_syls_wo_overhang, txt_overhanging_syls = (
            text_syls[: len(vol_syls) - 1],
            text_syls[len(vol_syls) - 1 :],
        )
        txt_joined_overhanging_syls = "".join(txt_overhanging_syls)
        text_syls = txt_syls_wo_overhang + [txt_joined_overhanging_syls]
        # Add spacing to volpiano to account for combining the
        # overhanging text syllables together into the final
        # syllable.
        vol_syls[-1] += "-" * (len(txt_joined_overhanging_syls) - len(vol_syls[-1]) + 1)
    # Pad text syllables with empty strings if more syllables in the
    # volpiano than in the text.
    comb_wrd = list(zip_longest(text_syls, vol_syls, fillvalue=""))
    return comb_wrd


def _align_section(
    text_section: List[List[str]], volpiano_section: str
) -> List[Tuple[str, str]]:
    """
    Aligns a section of text and volpiano, padding in case
    either text or volpiano is longer or shorter for that section.

    text_section [list[list[str]]]: nested list of syllabized text. Each
        sublist represents a word, and each element of the sublist represents
        a syllable (or unsyllabified phrase where text is not to be syllabified).
    volpiano_section [str]: volpiano string for the section

    returns [list[tuple[str, str]]]: list of tuples of text syllables and
        volpiano syllables
    """
    logging.debug("Aligning section - Text: %s", text_section)
    logging.debug("Aligning section - Volpiano: %s", volpiano_section)
    comb_section = []
    # For sections of missing music, of barline indicators, or of other
    # areas with unsyllabified texts (e.g., incipits) the text
    # should have a single unsyllabified element. If the text section has
    # more elements (an error), flatten the text section to a single string.
    first_text_word = text_section[0]
    first_text_syl = first_text_word[0]
    if (
        volpiano_section[0] in "346"
        or first_text_syl.startswith("~")
        or first_text_syl.startswith("[")
    ):
        if len(text_section) == 1 and len(first_text_word) == 1:
            comb_section.append((first_text_syl, volpiano_section))
        else:
            logging.debug("Text section has more than expected elements. Flattening.")
            flattened_section = []
            for word in text_section:
                flattened_section.extend(word)
            full_text = "".join(flattened_section)
            comb_section.append((full_text, volpiano_section))
    else:
        vol_words = VOLPIANO_WORD_REGEX.findall(volpiano_section)
        for txt_word, vol_word in zip_longest(text_section, vol_words, fillvalue="--"):
            if txt_word == "--":
                txt_word = [""]
            comb_wrd = _align_word(txt_word, vol_word)
            comb_section.extend(comb_wrd)
    logging.debug("Aligned section: %s", comb_section)
    return comb_section


def align_text_and_volpiano(
    chant_text: str,
    volpiano: str,
    text_presyllabified: bool = False,
    clean_text: bool = False,
) -> List[Tuple[str, str]]:
    """
    Aligns syllabified text with volpiano, performing periodic sanity checks
    and accounting for misalignments.

    chant_text [str]: the text of a chant
    volpiano [str]: the volpiano for a chant
    text_presyllabified [bool]: whether the text is already syllabified. Passed
        to syllabify_text (see that functions documentation for more details). Defaults
        to False.
    clean_text [bool]: whether to clean the text before syllabifying. Passed to
        syllabify_text (see that functions documentation for more details). Defaults
        to False.

    returns [list[tuple[str, str]]]: list of tuples of text syllables and volpiano syllables
        as (text_str, volpiano_str)
    """
    syllabified_text = syllabify_text(
        chant_text,
        clean_text=clean_text,
        flatten_result=False,
        text_presyllabified=text_presyllabified,
    )
    # Performs some validation on the passed volpiano string
    volpiano = _preprocess_volpiano(volpiano)
    # Section volpiano to match text sections returned by syllabify_text
    # Split at clefs, barlines, and missing music markers, removing empty
    # sections created by the split.
    volpiano_sections = VOLPIANO_SECTIONING_REGEX.split(volpiano)
    volpiano_sections = list(filter(lambda x: x != "", volpiano_sections))
    logging.debug("Volpiano sections: %s", volpiano_sections)
    if len(volpiano_sections) == len(syllabified_text) + 2:
        # Add the opening clef with no text
        comb_text_and_vol = [("", volpiano_sections[0])]
        # For each interior section, align the section
        for vol_sec, txt_sec in zip(volpiano_sections[1:-1], syllabified_text):
            aligned_section = _align_section(txt_sec, vol_sec)
            comb_text_and_vol.extend(aligned_section)
        # Add the final barline with no text
        comb_text_and_vol.append(("", volpiano_sections[-1]))
    else:
        raise ValueError(
            """Volpiano and text sections do not match. Ensure appropriate
            barlines and section markers are present in both."""
        )
    comb_text_and_vol = _postprocess_spacing(comb_text_and_vol)
    logging.debug("Combined text and volpiano: %s", comb_text_and_vol)
    return comb_text_and_vol
