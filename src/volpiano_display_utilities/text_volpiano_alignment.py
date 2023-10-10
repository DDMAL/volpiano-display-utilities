"""
Module that aligns the syllabified text and melody (encoded in volpiano) of a chant. This
module assumes that text and melody have been entered according to the conventions of Cantus
Database (more details about these conventions can be found 
at https://cantusdatabase.org/documents). See the README for more information.

Use align_text_and_volpiano to align the text and melody strings of a chant.
"""
import re
import logging
from itertools import zip_longest, takewhile
from typing import List, Tuple
from cantus_text_syllabification import syllabify_text

# A string containing all valid volpiano characters in Cantus
# Database. Used to check for invalid characters.
VALID_VOLPIANO_CHARS = "-19abcdefghijklmnopqrsyz)ABCDEFGHIJKLMNOPQRSYZ3467]"


def _preprocess_volpiano(volpiano_str: str) -> str:
    """
    Prepares volpiano string for alignment with text:
    - Checks for any invalid characters
    - Ensures proper spacing around barlines ("3" and "4") and missing
        music indicators ("6")
    - Ensures volpiano string has an ending barline ("3" or "4")

    volpiano_str [str]: volpiano string

    returns [str]: preprocessed volpiano string
    """
    processed_str = ""
    volpiano_str_len = len(volpiano_str)
    for i, char in enumerate(volpiano_str):
        # Check if char is valid
        if char not in VALID_VOLPIANO_CHARS:
            logging.debug("Removed invalid character (%s) in volpiano string.", char)
            continue
        # Check if char is a barline or missing music indicator and ensure
        # proper spacing
        if (char in "346") and (i != volpiano_str_len - 1):
            # Add proper spacing before barline
            while processed_str[-3:] != "---":
                processed_str += "-"
            # Add barline character
            processed_str += char
            # Add proper spacing after barline
            num_hyph_next = sum(
                1 for _ in takewhile(lambda x: x == "-", volpiano_str[i + 1 :])
            )
            processed_str += "-" * (3 - num_hyph_next)
            continue
        processed_str += char
    # Ensure volpiano string ends with a properly-spaced barline
    if processed_str[-4:] not in ["---3", "---4"]:
        processed_str = processed_str.rstrip("-") + "---3"
    logging.debug("Preprocessed volpiano string: %s", processed_str)
    return processed_str


def _postprocess_spacing(
    comb_text_and_vol: List[Tuple[str, str]],
) -> List[Tuple[str, str]]:
    """
    Handle some special spacing requirements for optimal display
    of volpiano with chant text.

    Ensures that:
     - the length of missing music sections responds to the length of
        the text associated with the section

    comb_text_and_vol [list[tuple[str, str]]]:
        list of tuples of text syllables and volpiano syllables

    returns [list[tuple[str, str]]]: list of tuples of text syllables and
        volpiano syllables with spacing of missing music sections responsive
        to associated text length
    """
    comb_text_and_vol_rev_spacing = []
    for text_elem, vol_elem in comb_text_and_vol:
        if vol_elem[0] == "6":
            text_length = len(text_elem)
            if text_length > 10:
                vol_elem = "6" + "-" * text_length + "6---"
        comb_text_and_vol_rev_spacing.append((text_elem, vol_elem))
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
    vol_syls = re.findall(r".*?-{2,3}", volpiano_word)
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
    # For sections with missing music, both text and volpiano should have
    # a single element (text is an unsyllabified phrase and volpiano has
    # a missing music indicator ("6")). If the text section has more elements
    # (an error), flatten the text section to a single string.
    if volpiano_section.startswith("6"):
        if len(text_section) == 0 and len(text_section[0]) == 0:
            comb_section.append((text_section[0][0], volpiano_section))
        else:
            logging.debug("Text section has more than expected elements. Flattening.")
            flattened_section = []
            for word in text_section:
                flattened_section.extend(word)
            full_text = "".join(flattened_section)
            comb_section.append((full_text, volpiano_section))
    # For unsyllabified sections of text, the text section section should have a single
    # element. If it does, align the complete volpiano section to this element. If not
    # (an error), flatten the text section to a single string and combine.
    elif text_section[0][0].startswith("~") or text_section[0][0].startswith("["):
        if len(text_section) == 0 and len(text_section[0]) == 0:
            comb_section.append((text_section[0][0], volpiano_section))
        else:
            logging.debug("Text section has more than expected elements. Flattening.")
            flattened_section = []
            for word in text_section:
                flattened_section.extend(word)
            full_text = "".join(flattened_section)
            comb_section.append((full_text, volpiano_section))
    # Otherwise, align the sections word by word.
    else:
        vol_words = re.findall(r".*?---", volpiano_section)
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
) -> List[Tuple[str, str]]:
    """
    Aligns syllabified text with volpiano, performing periodic sanity checks
    and accounting for misalignments.

    chant_text [str]: the text of a chant
    volpiano [str]: the volpiano for a chant
    text_presyllabified [bool]: whether the text is already syllabified. Passed
        to syllabify_text (see that functions documentation for more details). Defaults
        to False.

    returns [list[tuple[str, str]]]: list of tuples of text syllables and volpiano syllables
        as (text_str, volpiano_str)
    """
    syllabified_text = syllabify_text(
        chant_text,
        clean_text=False,
        flatten_result=False,
        text_presyllabified=text_presyllabified,
    )
    # Performs some validation on the passed volpiano string
    volpiano = _preprocess_volpiano(volpiano)
    # Section volpiano to match text sections returned by syllabify_text
    # Split at clefs, barlines, and missing music markers, removing empty
    # sections created by the split.
    volpiano_sections = re.split(r"([134]-*|6-{6}6-{3})", volpiano)
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
