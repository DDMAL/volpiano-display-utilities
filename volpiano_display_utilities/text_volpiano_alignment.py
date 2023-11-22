"""
Module that aligns the syllabified text and melody (encoded in volpiano) of a chant. This
module assumes that text and melody have been entered according to the conventions of Cantus
Database (more details about these conventions can be found 
at https://cantusdatabase.org/documents). See the README for more information.

Use align_text_and_volpiano to align the text and melody strings of a chant.
"""
import re
import logging
from itertools import zip_longest, accumulate, takewhile
from typing import List, Tuple
from .cantus_text_syllabification import syllabify_text

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
VOLPIANO_SECTIONING_REGEX = re.compile(r"([134][\-7]*|6[\-7]*6[\-7]*)")

VOLPIANO_WORD_REGEX = re.compile(r".*?-{3,}")

VOLPIANO_SYLLABLE_REGEX = re.compile(r".*?-{2,}")


def _preprocess_volpiano(raw_volpiano_str: str) -> Tuple[str, str, str]:
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

    returns Tuple[str, str, str]: preprocessed volpiano string without
        beginning clef or final barline, the clef
        at the beginning of the volpiano string, and the final barline
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
    return processed_vol, "1---", last_char


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
    comb_text_and_vol_rev_spacing: List[Tuple[str, str]] = []
    # Spacing for the opening clef and final barline of the
    # volpiano string are handled in the preprocessing function
    # so we don't need to deal with those here.
    beg_clef_section: Tuple[str, str] = comb_text_and_vol[0]
    fin_bar_section: Tuple[str, str] = comb_text_and_vol[-1]
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


def _syllabify_volpiano(volpiano: str) -> List[List[List[str]]]:
    """
    Split a volpiano string to match the structure of syllabified text
    from cantus_text_syllabification.syllabify_text.

    volpiano [str]: volpiano string

    returns [list[list[list[str]]]]: nested list of syllables. Each sublist
        represents a word, and each element of the sublist represents a syllable.
    """
    volpiano_sections: List[str] = VOLPIANO_SECTIONING_REGEX.split(volpiano)
    # Filter out empty sections created by the split
    volpiano_sections = list(filter(lambda x: x != "", volpiano_sections))
    syllabified_volpiano: List[List[List[str]]] = []
    for vol_sec in volpiano_sections:
        # We don't syllabify barlines or missing music markers
        if vol_sec[0] in "346":
            syllabified_volpiano.append([[vol_sec]])
            continue
        vol_words = VOLPIANO_WORD_REGEX.findall(vol_sec)
        syllabified_words: List[List[str]] = []
        for vol_word in vol_words:
            vol_syls = VOLPIANO_SYLLABLE_REGEX.findall(vol_word)
            syllabified_words.append(vol_syls)
        syllabified_volpiano.append(syllabified_words)
    return syllabified_volpiano


def _align_word(
    text_syls: List[str], volpiano_syls: List[str]
) -> List[Tuple[str, str]]:
    """
    Align a word of text and volpiano, padding in case
    either text or volpiano is longer or shorter for that word.

    text_syls [list[str]]: list of syllables in the word
    volpiano_syls [list[str]]: volpiano string for the word

    returns [list[tuple[str, str]]]: list of tuples of text syllables and
        volpiano syllables aligned together
    """
    # Squash final syllables of a word together if there are more
    # syllables in the text than in the volpiano.
    if len(text_syls) > len(volpiano_syls):
        txt_syls_wo_overhang, txt_overhanging_syls = (
            text_syls[: len(volpiano_syls) - 1],
            text_syls[len(volpiano_syls) - 1 :],
        )
        txt_joined_overhanging_syls = "".join(txt_overhanging_syls)
        text_syls = txt_syls_wo_overhang + [txt_joined_overhanging_syls]
        # Add spacing to volpiano to account for combining the
        # overhanging text syllables together into the final
        # syllable.
        volpiano_syls[-1] += "-" * (
            len(txt_joined_overhanging_syls) - len(volpiano_syls[-1]) + 1
        )
    # Pad text syllables with empty strings if more syllables in the
    # volpiano than in the text.
    comb_wrd: List[Tuple[str, str]] = list(
        zip_longest(text_syls, volpiano_syls, fillvalue="")
    )
    return comb_wrd


def _align_section(
    text_section: List[List[str]], volpiano_section: List[List[str]]
) -> List[Tuple[str, str]]:
    """
    Aligns a section of text and volpiano, padding in case
    either text or volpiano is longer or shorter for that section.

    text_section [list[list[str]]]: nested list of syllabized text. Each
        sublist represents a word, and each element of the sublist represents
        a syllable (or unsyllabified phrase where text is not to be syllabified).
    volpiano_section [list[list[str]]]: volpiano string for the section

    returns [list[tuple[str, str]]]: list of tuples of text syllables and
        volpiano syllables
    """
    logging.debug("Aligning section - Text: %s", text_section)
    logging.debug("Aligning section - Volpiano: %s", volpiano_section)
    comb_section: List[Tuple[str, str]] = []
    # For sections of missing music, of barline indicators, or of other
    # areas with unsyllabified texts (e.g., incipits) the text
    # should have a single unsyllabified element. If the text section has
    # more elements (an error), flatten the text section to a single string.
    # This is aligned to all the volpiano in the section (during the
    # volpiano syllabification step, the volpiano will either have stayed
    # a single syllable in the case of missing music or a pipe "|"
    # or have been split into multiple syllables in the case of other
    # unsyllabified text)
    first_text_word = text_section[0]
    first_text_syl = first_text_word[0]
    first_vol_word = volpiano_section[0]
    first_vol_syl = first_vol_word[0]
    if (
        first_vol_syl[0] in "346"
        or first_text_syl.startswith("~")
        or first_text_syl.startswith("[")
    ):
        logging.debug("Aligning section with unsyllabified text.")
        volpiano_section_flattened = "".join(
            "".join(vol_word) for vol_word in volpiano_section
        )
        if len(text_section) == 1 and len(first_text_word) == 1:
            comb_section.append((first_text_syl, volpiano_section_flattened))
        else:
            logging.debug("Text section has more than expected elements. Flattening.")
            flattened_section = []
            for word in text_section:
                flattened_section.extend(word)
            full_text = "".join(flattened_section)
            comb_section.append((full_text, volpiano_section_flattened))
    else:
        for txt_word, vol_word in zip_longest(
            text_section, volpiano_section, fillvalue=["--"]
        ):
            if txt_word == ["--"]:
                txt_word = [""]
            comb_wrd = _align_word(txt_word, vol_word)
            comb_section.extend(comb_wrd)
    logging.debug("Aligned section: %s", comb_section)
    return comb_section


def _infer_barlines(
    syllabified_text: List[List[List[str]]], syllabified_volpiano: List[List[List[str]]]
) -> Tuple[List[List[List[str]]], List[List[List[str]]]]:
    """
    Infers additional barlines when the number of text and volpiano sections
    do not match: wherever there is a barline in either the text or the volpiano,
    we ensure there is a barline in the other. This is done by inserting a barline
    in the part "missing" the barline to create a section containing as close to the
    same number of syllables (breaking at the whole word) as possible to the section
    in the part containing the barline. All barlines encoded in the original strings
    are maintained.

    This logic provides a "correct" alignment in cases where a barline was simply not
    encoded in one part, but where encoding otherwise aligns (see test cases
    "Test alignment: Volpiano missing section barlines" and "Test alignment:
    Text missing section barlines") and an "incorrect" but still readable
    alignment in cases where other encoding errors are also present (for
    example, a missing barline in one part and a missing word break in the other; see
    "Test alignment: Volpiano missing section barlines with syllable mismatch" and
    "Test alignment: Text missing section barlines with syllable mismatch").
    """
    vol_w_inferred_barlines: List[List[List[str]]] = []
    text_w_inferred_barlines: List[List[List[str]]] = []
    while len(syllabified_text) > 0 and len(syllabified_volpiano) > 0:
        text_words: List[List[str]] = syllabified_text.pop(0)
        vol_words: List[List[str]] = syllabified_volpiano.pop(0)
        # acc_text_syls and acc_vol_syls are cummulative counts, by word,
        # of the number of syllables in text_section and vol_section, respectively
        acc_text_syls: List[int] = list(
            accumulate([len(txt_word) for txt_word in text_words])
        )
        acc_vol_syls: List[int] = list(
            accumulate([len(vol_word) for vol_word in vol_words])
        )
        num_text_syls: int = acc_text_syls[-1]
        num_vol_syls: int = acc_vol_syls[-1]
        logging.debug("Text section: %s Volpiano section: %s", text_words, vol_words)
        # If equal number of syllables in the sections,
        # keep the sections as they are and remove them from
        # the lists of sections to be aligned.
        if num_text_syls == num_vol_syls:
            vol_w_inferred_barlines.append(vol_words)
            text_w_inferred_barlines.append(text_words)
            logging.debug(
                "Volpiano and text sections have equal number of syllables. No barline needed."
            )
        # If there are more syllables in the text than in the volpiano,
        # insert a barline in the volpiano to create a section with
        # the same number of syllables as the text section.
        elif num_vol_syls < num_text_syls:
            logging.debug(
                "Text section has more syllables than volpiano section. Inferring barline in text."
            )
            len_txt_sect_1 = len(
                list(takewhile(lambda x: x < num_vol_syls, acc_text_syls))
            )
            if abs(num_vol_syls - acc_text_syls[len_txt_sect_1 - 1]) > abs(
                num_vol_syls - acc_text_syls[len_txt_sect_1]
            ):
                len_txt_sect_1 += 1
            vol_w_inferred_barlines.append(vol_words)
            text_w_inferred_barlines.append(text_words[:len_txt_sect_1])
            syllabified_text.insert(0, text_words[len_txt_sect_1:])
            syllabified_text.insert(0, [["|"]])
            logging.debug("New text section: %s", text_words[:len_txt_sect_1])
        # If there are more syllables in the volpiano than in the text,
        # insert a barline in the text to create a section with the same
        # number of syllables as the text section.
        elif num_vol_syls > num_text_syls:
            logging.debug(
                "Volpiano section has more syllables than text section. Inferring barline in volpiano."
            )
            len_vol_sect_1 = len(
                list(takewhile(lambda x: x < num_text_syls, acc_vol_syls))
            )
            if abs(num_text_syls - acc_vol_syls[len_vol_sect_1 - 1]) > abs(
                num_text_syls - acc_vol_syls[len_vol_sect_1]
            ):
                len_vol_sect_1 += 1
            vol_w_inferred_barlines.append(vol_words[:len_vol_sect_1])
            syllabified_volpiano.insert(0, vol_words[len_vol_sect_1:])
            syllabified_volpiano.insert(0, [["3---"]])
            text_w_inferred_barlines.append(text_words)
            logging.debug("New volpiano section: %s", vol_words[:len_vol_sect_1])
    # If there are any remaining sections in either the text or volpiano,
    # add them to the final section of the appropriate list.
    if len(syllabified_text) > 0:
        for sect in syllabified_text:
            text_w_inferred_barlines[-1].extend(sect)
    elif len(syllabified_volpiano) > 0:
        for sect in syllabified_volpiano:
            vol_w_inferred_barlines[-1].extend(sect)
    return text_w_inferred_barlines, vol_w_inferred_barlines


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
    syllabified_text: List[List[List[str]]] = syllabify_text(
        chant_text,
        clean_text=clean_text,
        flatten_result=False,
        text_presyllabified=text_presyllabified,
    )
    # Performs some validation on the passed volpiano string
    preprocessed_volpiano, clef, fin_bar = _preprocess_volpiano(volpiano)
    syllabified_volpiano = _syllabify_volpiano(preprocessed_volpiano)
    # Add the opening clef with no text
    comb_text_and_vol = [("", clef)]
    logging.debug("Syllabified volpiano: %s", syllabified_volpiano)
    if len(syllabified_volpiano) != len(syllabified_text):
        logging.debug(
            "Different number of text and volpiano sections. Inferring barlines."
        )
        syllabified_text, syllabified_volpiano = _infer_barlines(
            syllabified_text, syllabified_volpiano
        )
    # For each interior section, align the section
    for vol_sec, txt_sec in zip(syllabified_volpiano, syllabified_text):
        aligned_section: List[Tuple[str, str]] = _align_section(txt_sec, vol_sec)
        comb_text_and_vol.extend(aligned_section)
    # Add the final barline with no text
    comb_text_and_vol.append(("", fin_bar))
    aligned_txt_and_vol: List[Tuple[str, str]] = _postprocess_spacing(comb_text_and_vol)
    logging.debug("Combined text and volpiano: %s", aligned_txt_and_vol)
    return aligned_txt_and_vol
