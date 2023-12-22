"""
Module that aligns the syllabified text and melody (encoded in volpiano) of a chant. This
module assumes that text and melody have been entered according to the conventions of Cantus
Database (more details about these conventions can be found 
at https://cantusdatabase.org/documents). See the README for more information.

Use align_text_and_volpiano to align the text and melody strings of a chant.
"""
import logging
from itertools import zip_longest
from typing import List, Tuple, TypeVar
from .cantus_text_syllabification import syllabify_text
from .syllabified_section import SyllabifiedTextSection, SyllabifiedVolpianoSection
from .volpiano_syllabification import (
    syllabify_volpiano,
    preprocess_volpiano,
    adjust_music_spacing,
    adjust_missing_music_spacing,
)

T = TypeVar("T", str, List)


def _zip_and_align(
    text: List[T], volpiano: List[T], pad_text: T, pad_volpiano: T
) -> List[Tuple[T, T]]:
    """
    Aligns lists of text and volpiano together and adds padding
    if necessary. Can be used to align sections (in which case the
    text and volpiano arguments are lists of lists) or words (in which
    case the text and volpiano arguments are lists of strings).

    text [list[T]]: text list
    volpiano [list[T]]: volpiano list
    pad_text [T]: value to fill text with if text is shorter than volpiano
    pad_volpiano [T]: value to fill volpiano with if volpiano is shorter than text

    returns [list[tuple[T, T]]]: zipped list with padding
    """
    len_text = len(text)
    len_volpiano = len(volpiano)
    if len_text == len_volpiano:
        logging.debug(
            "Text and volpiano have equal number of words: zipped with no padding."
        )
        return list(zip(text, volpiano))
    if len_text > len_volpiano:
        logging.debug("Text longer than volpiano: padding volpiano.")
        return list(zip_longest(text, volpiano, fillvalue=pad_volpiano))
    logging.debug("Volpiano longer than text: padding text.")
    return list(zip_longest(text, volpiano, fillvalue=pad_text))


def _align_word(text: List[str], volpiano: List[str]) -> List[Tuple[str, str]]:
    zipped_word = _zip_and_align(text, volpiano, pad_text="", pad_volpiano="---")
    aligned_word = []
    for text_syl, vol_syl in zipped_word[:-1]:
        vol_syl = adjust_music_spacing(vol_syl, len(text_syl), False)
        aligned_word.append((text_syl, vol_syl))
    text_syl, vol_syl = zipped_word[-1]
    vol_syl = adjust_music_spacing(vol_syl, len(text_syl), True)
    aligned_word.append((text_syl, vol_syl))
    return aligned_word


def _align_section(
    text_section: SyllabifiedTextSection,
    volpiano_section: SyllabifiedVolpianoSection,
) -> List[Tuple[str, str]]:
    """
    Aligns a section of text and volpiano, padding in case
    either text or volpiano is longer or shorter for that section.
    """
    logging.debug(
        "Aligning section - Text: %s. Volpiano: %s", text_section, volpiano_section
    )
    comb_section: List[Tuple[str, str]] = []
    # For sections of missing music, of barline indicators, or of other
    # areas with unsyllabified texts (e.g., incipits) the text
    # should have a single unsyllabified element.
    # This is aligned to all the volpiano in the section.
    if not text_section.is_syllabified:
        logging.debug("Aligning section with unsyllabified text.")
        unsyllabified_text = text_section.get_syllable(word_num=0, syllable_num=0)
        # The volpiano section is flattened to a string prior
        # to alignment with the text. Additional processing on
        # the volpiano section depends on the volpiano contents:
        # - If the volpiano section is a barline, we make sure
        #  that the section terminates wih the proper spacing.
        # - If the volpiano section is missing music, we make sure
        #  that the section is properly sized the length of the
        #  accompanying text.
        # - If neither, no additional processing occurs.
        flattened_volpiano = volpiano_section.flatten_to_str()
        if volpiano_section.is_barline:
            processed_volpiano = adjust_music_spacing(
                flattened_volpiano, len(unsyllabified_text), True
            )
            comb_section.append((unsyllabified_text, processed_volpiano))
        elif volpiano_section.is_missing_music:
            processed_volpiano = adjust_missing_music_spacing(
                flattened_volpiano, len(unsyllabified_text)
            )
            comb_section.append((unsyllabified_text, processed_volpiano))
        else:
            comb_section.append((unsyllabified_text, flattened_volpiano))
    else:
        # In sections of syllabified text, align text and volpiano
        # word by word.
        logging.debug("Aligning words in section with syllabified text.")
        aligned_words = _zip_and_align(
            text_section.section,
            volpiano_section.section,
            pad_text=[""],
            pad_volpiano=["----"],
        )
        logging.debug("Aligned words: %s", aligned_words)
        for txt_word, vol_word in aligned_words:
            # Align each word of text and volpiano in the section
            # syllable by syllable.
            logging.debug(
                "Aligning syllables in word. Text: %s. Volpiano: %s", txt_word, vol_word
            )
            comb_wrd = _align_word(txt_word, vol_word)
            logging.debug("Aligned syllables: %s", comb_wrd)
            comb_section.extend(comb_wrd)
    logging.debug("Aligned section: %s", comb_section)
    return comb_section


def _add_text_barline(
    syllabified_str: List[SyllabifiedTextSection],
    section_to_split_idx: int,
    split_word_idx: int,
) -> List[SyllabifiedTextSection]:
    section_to_split = syllabified_str[section_to_split_idx]
    logging.debug(
        "Adding barline to text %s at word %s", section_to_split, split_word_idx
    )
    syllabified_str[section_to_split_idx] = SyllabifiedTextSection(
        section_to_split.section[:split_word_idx]
    )
    syllabified_str.insert(section_to_split_idx + 1, SyllabifiedTextSection([["|"]]))
    syllabified_str.insert(
        section_to_split_idx + 2,
        SyllabifiedTextSection(section_to_split.section[split_word_idx:]),
    )
    return syllabified_str


def _add_volpiano_barline(
    syllabified_str: List[SyllabifiedVolpianoSection],
    section_to_split_idx: int,
    split_word_idx: int,
) -> List[SyllabifiedVolpianoSection]:
    section_to_split = syllabified_str[section_to_split_idx]
    logging.debug(
        "Adding barline to volpiano %s at word %s", section_to_split, split_word_idx
    )
    syllabified_str[section_to_split_idx] = SyllabifiedVolpianoSection(
        section_to_split.section[:split_word_idx]
    )
    syllabified_str.insert(
        section_to_split_idx + 1, SyllabifiedVolpianoSection([["3---"]])
    )
    syllabified_str.insert(
        section_to_split_idx + 2,
        SyllabifiedVolpianoSection(section_to_split.section[split_word_idx:]),
    )
    return syllabified_str


def _infer_barlines(
    syllabified_text: List[SyllabifiedTextSection],
    syllabified_volpiano: List[SyllabifiedVolpianoSection],
) -> Tuple[List[SyllabifiedTextSection], List[SyllabifiedVolpianoSection]]:
    """
    Infer barlines in cases where the number of text and volpiano sections
    do not match. We assume that this is the case where a barline was omitted
    in either string; other cases that might result in a section mismatch (e.g.,
    improperly encoded text aligned with missing music) are more complex and not
    inferred here.
    """
    num_barlines_text = sum(section.is_barline for section in syllabified_text)
    num_barlines_volpiano = sum(section.is_barline for section in syllabified_volpiano)
    if num_barlines_text == num_barlines_volpiano:
        raise ValueError(
            "Text and volpiano have equal number of barlines. Section alignment cannot be inferred."
        )
    while num_barlines_text != num_barlines_volpiano:
        num_words_diff: List[int] = [
            abs(text_sec.num_words - vol_sec.num_words)
            for text_sec, vol_sec in zip(syllabified_text, syllabified_volpiano)
        ]
        max_diff_idx = num_words_diff.index(max(num_words_diff))
        if num_barlines_text > num_barlines_volpiano:
            logging.debug(
                "Text has more barlines than volpiano. Inferring additional barline in volpiano."
            )
            syllabified_volpiano = _add_volpiano_barline(
                syllabified_volpiano,
                max_diff_idx,
                syllabified_text[max_diff_idx].num_words,
            )
        else:
            logging.debug(
                "Volpiano has more barlines than text. Inferring additional barline in text."
            )
            syllabified_text = _add_text_barline(
                syllabified_text,
                max_diff_idx,
                syllabified_volpiano[max_diff_idx].num_words,
            )
        # Update numbers of barlines for next step in loop
        num_barlines_text = sum(1 for section in syllabified_text if section.is_barline)
        num_barlines_volpiano = sum(
            1 for section in syllabified_volpiano if section.is_barline
        )
    return syllabified_text, syllabified_volpiano


def align_text_and_volpiano(
    chant_text: str, volpiano: str, clean_text: bool, text_presyllabified: bool = False
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
        chant_text, clean_text=clean_text, text_presyllabified=text_presyllabified
    )
    preprocessed_volpiano, fin_bar = preprocess_volpiano(volpiano)
    syllabified_volpiano = syllabify_volpiano(preprocessed_volpiano)
    # Add the opening clef with no text
    alignment: List[Tuple[str, str]] = [("", "1---")]
    # If the number of sections in the text and volpiano do not match,
    # we need to infer section breaks in the shorter of the strings
    # in order to align them.
    if len(syllabified_text) != len(syllabified_volpiano):
        logging.debug(
            "Text and volpiano have different numbers of sections. Inferring barlines."
        )
        syllabified_text, syllabified_volpiano = _infer_barlines(
            syllabified_text, syllabified_volpiano
        )
    # For each interior section, align the section
    for vol_sec, txt_sec in zip(syllabified_volpiano, syllabified_text):
        aligned_section: List[Tuple[str, str]] = _align_section(txt_sec, vol_sec)
        alignment.extend(aligned_section)
    # Add the final barline with no text
    alignment.append(("", fin_bar))
    logging.debug("Combined text and volpiano: %s", alignment)
    return alignment
