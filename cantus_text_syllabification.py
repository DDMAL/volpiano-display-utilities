"""
A utility to syllabify chant texts so that they can be aligned
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
}

# Pre-compiled regex patterns used in this module
# Matches any character not valid in Cantus DB entries
INVALID_CHAR_REGEX = re.compile(r"[^a-zA-Z#~\{\}\[\]\|\- ]")
STR_BEGINS_W_HYPHEN_REGEX = re.compile(r"^\-")
STR_ENDS_W_HYPHEN_REGEX = re.compile(r"\-$")
STR_STARTS_OR_ENDS_W_HYPHEN_REGEX = re.compile(r"(^\-)|(\-$)")
# Split by (and capture) text surrounded by curly brackets or square brackets
# or pipes.
TEXT_SECTIONER_REGEX = re.compile(r"(\{.*?\}|\[.*?\]|\|)")


def _clean_text(test: str) -> str:
    """
    Removes invalid characters from the text string.

    test [str]: string to clean

    returns [str]: cleaned string
    """
    return INVALID_CHAR_REGEX.sub("", test)


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
    word_str = word_str.lower()
    return word_str, bool(start_hyphen), bool(end_hyphen)


def _get_text_sections(text: str) -> "list[str]":
    """
    Splits a text string into sections based on the presence of
    curly braces "{}", square brackets "[]",
    and pipes "|". These special characters
    are captures in the sections and sections that are just a space
    are removed.

    text [str]: text to split

    returns [list[str]]: list of text sections
    """
    text_sections = TEXT_SECTIONER_REGEX.split(text)
    # Somtimes splitting can result in empty strings
    text_sections = list(filter(lambda x: x != "", text_sections))
    return text_sections


def syllabify_text(
    text: str,
    clean_text: bool = False,
    stringify_result: bool = False,
    flatten_result=False,
) -> "list[list[str]]":
    """
    Syllabifies a text string that has been encoded in the style
    of the Cantus Database. Texts are syllabified word by word,
    except in special cases outlined in the README.

    text [str]: text to syllabify
    clean_text [bool]: if True, removes invalid characters from
        the text string; if False, raises a ValueError if invalid
        characters are detected
    stringify_result [bool]: if True, returns a string of the
        syllabified text instead of a list of lists with hyphens separating
        syllables in syllabified substrings
    flatten_result [bool]: if True, flattens the list of lists
        into a single list of strings (syllables and unsyllabified
        units)

    returns [list[list[str]]]: syllabified text
    """
    logging.debug("Syllabifying text: %s", text)
    if clean_text:
        text = _clean_text(text)
        logging.debug("Cleaned text: %s", text)
    else:
        if _detect_invalid_characters(text):
            raise ValueError(
                "Invalid characters detected in text string. To clean, use clean_text=True."
            )
    text_sections = _get_text_sections(text)
    logging.debug("Text sections: %s", text_sections)
    syllabified_text = []
    for text_section in text_sections:
        if text_section == "|" or text_section[0] in ("{", "["):
            syllabified_text.append([text_section])
            logging.debug("Text section not syllabified: %s", text_section)
        else:
            words = text_section.split(" ")
            words = list(filter(lambda x: x != "", words))
            for word in words:
                if word == "#" or word[0] == "~":
                    syllabified_text.append([word])
                    logging.debug("Word not syllabified: %s", word)
                elif word in EXCEPTIONS_DICT:
                    syllabified_text.append(EXCEPTIONS_DICT[word])
                    logging.debug(
                        "Cantus Database syllabification exception found: %s", word
                    )
                else:
                    (
                        prepared_word,
                        start_hyphen,
                        end_hyphen,
                    ) = _prepare_string_for_syllabification(word)
                    word_syllable_boundaries = syllabify_word(
                        prepared_word, return_syllabified_string=False
                    )
                    dehyphenated_word = STR_STARTS_OR_ENDS_W_HYPHEN_REGEX.sub("", word)
                    syllabified_word = split_word_by_syl_bounds(
                        dehyphenated_word, word_syllable_boundaries
                    )
                    if start_hyphen:
                        syllabified_word[0] = f"-{syllabified_word[0]}"
                    elif end_hyphen:
                        syllabified_word[-1] = f"{syllabified_word[-1]}-"
                    syllabified_text.append(syllabified_word)
    logging.debug("Syllabified text: %s", syllabified_text)
    if stringify_result:
        syllabified_text = stringify_syllabified_text(syllabified_text)
    if flatten_result:
        syllabified_text = flatten_syllabified_text(syllabified_text)
    return syllabified_text


def flatten_syllabified_text(syllabified_text: "list[list[str]]") -> "list[str]":
    """
    Courtesy function that flattens the output of syllabify_text
    into a single list of syllables.

    syllabified_text list[list[str]]: output of syllabify_text

    returns [list[str]]: flattened list of syllables
    """
    flattened_syl_list = []
    for word in syllabified_text:
        flattened_syl_list.extend(word)
    return flattened_syl_list


def stringify_syllabified_text(syllabified_text: "list[list[str]]") -> str:
    """
    Courtesy function that flattens the output of syllabify_text
    into a single string of syllables with syllables separated by
    hyphens.

    syllabified_text list[list[str]]: output of syllabify_text

    returns [str]: flattened string of syllables
    """
    word_list = ["".join(word) for word in syllabified_text]
    return " ".join(word_list)
