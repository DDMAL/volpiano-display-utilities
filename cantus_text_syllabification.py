"""
Module that syllabifies chant texts so that they can be aligned
with melodies stored in Cantus Database. This utility assumes transcription
conventions of CantusDB (found in the "Text Entry and Editing" pdf
at https://cantus.uwaterloo.ca/documents), including the use of 
special characters to indicate missing text, missing music, incipits,
and other alginment details. See the README for more information.

Use syllabify_text to syllabify a text string. See function docstring
or README for more details.
"""

import re
import logging
from typing import Union

from latin_word_syllabification import syllabify_word, split_word_by_syl_bounds

EXCEPTIONS_DICT = {
    "euouae": ["e-", "u-", "o-", "u-", "a-", "e"],
    "israelitis": ["is-", "ra-", "e-", "li-", "tis"],
    "israel": ["is-", "ra-", "el"],
    "michael": ["mi-", "cha-", "el"],
}

# Pre-compiled regex patterns used in this module
# INVALID_CHAR_REGEX matches any character not valid in Cantus DB entries
INVALID_CHAR_REGEX = re.compile(r"[^a-zA-Z#~\{\}\[\]\|\- ]")
# Matches a string that begins with a hyphen
STR_BEGINS_W_HYPHEN_REGEX = re.compile(r"^\-")
# Matches a string that ends with a hyphen
STR_ENDS_W_HYPHEN_REGEX = re.compile(r"\-$")
# Matches pipes and missing music sectioners ("{" and "}")
TEXT_SECTIONER_REGEX = re.compile(r"(\||\{.*?\}(?!\s*?\{))")


def _clean_text(text: str) -> str:
    """
    Removes invalid characters from the text string.

    text [str]: string to clean

    returns [str]: cleaned string
    """
    return INVALID_CHAR_REGEX.sub("", text)


def _detect_invalid_characters(text: str) -> bool:
    """
    Detects invalid characters in the text string.

    text [str]: string to check

    returns [bool]: True if invalid characters are present, False otherwise
    """
    return bool(INVALID_CHAR_REGEX.search(text))


def _prepare_string_for_syllabification(word_str: str) -> "tuple[str, bool, bool]":
    """
    Complete preparation of a string before syllabification.
    All letters are converted to lowercase. Hyphens are removed
    from the beginning and end of the string, and the presence
    of these hyphens is recorded.

    word_str [str]: string to prepare

    returns [tuple[str,bool,bool]]: prepared string, whether a hyphen
        was removed from the beginning of the string, whether a hyphen
        was removed from the end of the string
    """
    word_str, start_hyphen = STR_BEGINS_W_HYPHEN_REGEX.subn("", word_str)
    word_str, end_hyphen = STR_ENDS_W_HYPHEN_REGEX.subn("", word_str)
    return word_str, bool(start_hyphen), bool(end_hyphen)


def _split_text_sections(text: str) -> "list[str]":
    """
    Splits a text string into sections based on the presence of
    curly braces "{}", square brackets "[]",
    and pipes "|". These special characters
    are captured in the sections.

    text [str]: text to split

    returns [list[str]]: list of text sections
    """
    text_sections = TEXT_SECTIONER_REGEX.split(text)
    # Remove extra spaces from sections and remove empty sections/None-type sections
    # caused by section split.
    text_sections = [section.strip() for section in text_sections if section.strip()]
    return text_sections


def syllabify_text(
    text: str,
    clean_text: bool = False,
    flatten_result: bool = False,
) -> Union["list[list[str]]", str]:
    """
    Syllabifies a text string that has been encoded in the style
    of the Cantus Database. Texts are syllabified word by word,
    except in special cases outlined in the README.

    text [str]: text to syllabify
    clean_text [bool]: if True, removes invalid characters from
        the text string; if False, raises a ValueError if invalid
        characters are detected
    flatten_result [bool]: if True, returns a string of the
        syllabified text (instead of a list of lists) with hyphens separating
        syllables in syllabified substrings. See returns for more details.

    returns [list[list[list[str]]] or str]: by default, a nested list of strings.
    The return value is a list of text sections, each containing a list of "words"
    (these may be actual words, symbols like "|", or strings of text that won't be
    syllabified). Each "word" is a list of syllables. If flatten_result is True, the
    syllabified text is returned as a single string with hyphens separating syllables.

    For example:
    >>> syllabify_text("Ave Maria | ~gratia [plena] | Dominus tecum", flatten_result=False)
    [[['A', 've'], ['Ma', 'ri', 'a']], [['|']], [['~gratia'], ['[plena]']], [['|']], [['Do', 'mi', 'nus'], ['te', 'cum']]]
    >>> syllabify_text("Ave Maria | ~gratia [plena] | Dominus tecum", flatten_result=True)
    'A-ve Ma-ri-a | ~gratia [plena] | Do-mi-nus te-cum'
    """

    logging.debug("Syllabifying text: %s", text)
    # Check for invalid characters and clean text if requested
    if clean_text:
        text = _clean_text(text)
        logging.debug("Cleaned text: %s", text)
    else:
        if _detect_invalid_characters(text):
            raise ValueError(
                "Invalid characters detected in text string. To clean, use clean_text=True."
            )
    # Split text into sections. Sections are divided by pipes ("|") or enclosed
    # in curly braces ("{}") or square brackets ("[]").
    text_sections = _split_text_sections(text)
    logging.debug("Text sections: %s", text_sections)
    syllabified_text = []
    for text_section in text_sections:
        # We don't syllabify text sections that are enclosed in curly braces,
        # square brackets, or begin with a tilde. We also don't syllabify pipes themselves.
        syllabified_section = []
        if text_section == "|" or text_section[0] in "{~[":
            syllabified_section.append([text_section])
            syllabified_text.append(syllabified_section)
            logging.debug("Text section not syllabified: %s", text_section)
            continue
        words = text_section.split(" ")
        words = list(filter(lambda x: x != "", words))
        for word in words:
            # Don't syllabify the missing text symbol ("#")
            if word == "#":
                syllabified_section.append([word])
                logging.debug("Word not syllabified: %s", word)
            # If the word is an exception, syllabify as specified
            elif word in EXCEPTIONS_DICT:
                syllabified_section.append(EXCEPTIONS_DICT[word])
                logging.debug(
                    "Cantus Database syllabification exception found: %s", word
                )
            else:
                # Record presence of and remove leading and trailing hyphens
                # from words
                (
                    prepared_word,
                    start_hyphen,
                    end_hyphen,
                ) = _prepare_string_for_syllabification(word)
                word_syllable_boundaries = syllabify_word(
                    prepared_word, return_string=False
                )
                syllabified_word = split_word_by_syl_bounds(
                    prepared_word, word_syllable_boundaries
                )
                # Re-add leading or trailing hyphens from words if necessary
                if start_hyphen:
                    syllabified_word[0] = f"-{syllabified_word[0]}"
                if end_hyphen:
                    syllabified_word[-1] = f"{syllabified_word[-1]}-"
                syllabified_section.append(syllabified_word)
        syllabified_text.append(syllabified_section)
    logging.debug("Syllabified text: %s", syllabified_text)
    if flatten_result:
        syllabified_text = stringify_syllabified_text(syllabified_text)
    return syllabified_text


def stringify_syllabified_text(syllabified_text: "list[list[str]]") -> str:
    """
    Courtesy function that flattens the output of syllabify_text
    into a single string of syllables with syllables separated by
    hyphens.

    syllabified_text list[list[list[[str]]]: syllabified text in the default
    output format of syllabify_text

    returns [str]: string of syllabified text
    """
    joined_sections = [
        ["".join(word) for word in section] for section in syllabified_text
    ]
    return " ".join([" ".join(section) for section in joined_sections])
