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
from typing import Tuple, List, cast, Optional

from .latin_word_syllabification import syllabify_word, split_word_by_syl_bounds
from .kanienkeha_word_syllabification import kanienkeha_syllabify_word
from .syllabified_section import SyllabifiedTextSection

EXCEPTIONS_DICT = {
    # Exceptions to usual word syllabification
    # Values are syllable boundaries (eg. a syllable
    # boundary should exist before the indicated
    # string index in the word)
    # Example: "mihi" has a syllable boundary before
    # the "h" (index 2), so we would have
    # "mihi":[2]
    "euouae": [1, 2, 3, 4, 5],
    "israelitis": [2, 4, 5, 7],
    "israel": [2, 4],
    "michael": [2, 5],
    "noe": [2],
}

# INVALID_CHAR_REGEX matches any character not valid in Cantus DB entries
INVALID_CHAR_REGEX = re.compile(r"[^\w#~\{\}\[\]\|\- 8]")
# Matches a string that begins with a hyphen
STR_BEGINS_W_HYPHEN_REGEX = re.compile(r"^\-")
# Matches a string that ends with a hyphen
STR_ENDS_W_HYPHEN_REGEX = re.compile(r"\-$")
# Matches pipes and missing music sectioners ("{" and "}" or "[" and "]", except
# when the latter is an incipit, denoted by a section beginning with a tilde "~")
TEXT_SECTIONER_REGEX = re.compile(r"(\||\{.*?\}|~.*?(?=\||$)|\[.*\])")
# Matches all hashes and preceding spaces, if any, except
# hashes that are immediately preceded by an open curly brace or
# the start of the string
SPACE_PRECEDING_HASH_REGEX = re.compile(r"(?<=[^\{]) ?#")
# Matches all hashes and following spaces, if any, except
# hashes that are immediately followed by a close curly brace or
# the end of the string
SPACE_FOLLOWING_HASH_REGEX = re.compile(r"# ?(?=[^\}])")


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


def _space_hash_signs(text: str) -> Tuple[str, bool]:
    """
    Spaces out hash signs ("#") in a text string to
    ensure that they are syllabified as individual
    words.

    text [str]: text string to space out

    returns [str, bool]: text string with hash signs spaced out
        and boolean indicating whether spacing adjustments
        were made
    """
    spaced_text = SPACE_PRECEDING_HASH_REGEX.sub(" #", text)
    spaced_text = SPACE_FOLLOWING_HASH_REGEX.sub("# ", spaced_text)
    adjusted = spaced_text != text
    return spaced_text, adjusted


def _prepare_string_for_syllabification(word_str: str) -> Tuple[str, bool, bool]:
    """
    Complete preparation of a word string before syllabification.
    Hyphens are removed from the beginning and end of the string,
    and the presence of these hyphens is recorded.

    word_str [str]: string containing a word (or partial word) to prepare

    returns [tuple[str,bool,bool]]: prepared string, whether a hyphen
        was removed from the beginning of the string, whether a hyphen
        was removed from the end of the string
    """
    word_str, start_hyphen = STR_BEGINS_W_HYPHEN_REGEX.subn("", word_str)
    word_str, end_hyphen = STR_ENDS_W_HYPHEN_REGEX.subn("", word_str)
    return word_str, bool(start_hyphen), bool(end_hyphen)


def _split_text_sections(text: str) -> List[str]:
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
    text_presyllabified: bool = False,
    language: Optional[str] = None,
) -> Tuple[List[SyllabifiedTextSection], bool]:
    """
    Syllabifies a text string that has been encoded in the style
    of the Cantus Database. Texts are syllabified word by word,
    except in special cases outlined in the README.

    text [str]: text to syllabify
    clean_text [bool]: if True, removes invalid characters from
        the text string; if False, raises a ValueError if invalid
        characters are detected
    text_presyllabified [bool]: if True, assumes that an already syllabified
        text string has been passed.  This is useful for cases
        where a CantusDB user has edited the syllabification of a chant text that
        then needs to be aligned with a melody. Already syllabified chant texts
        stored in CantusDB are strings with syllable breaks indicated by hyphens ("-").
        This function finds a syllable split if and only if a hyphen is
        present (ie. no additional syllabification is performed).

    returns [SyllabifiedTextSection, bool]: an object of class SyllabifiedTextSection
        that contains the syllabified text string and a boolean indicating whether
        spacing adjustments. See class docstring for more information.
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
    # Space out hash signs if necessary
    text, spacing_adjusted = _space_hash_signs(text)
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
            syllabified_text.append(SyllabifiedTextSection(syllabified_section))
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
            elif word.lower() in EXCEPTIONS_DICT:
                exception_syllabification = split_word_by_syl_bounds(
                    word, EXCEPTIONS_DICT[word.lower()]
                )
                syllabified_section.append(exception_syllabification)
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
                if text_presyllabified:
                    syls = prepared_word.split("-")
                    syllabified_word = [
                        f"{syl}-" if i != len(syls) - 1 else syl
                        for i, syl in enumerate(syls)
                    ]
                    logging.debug("Presyllabified word: %s", word)
                else:
                    if language == "kanienkeha":
                        word_syllable_boundaries = cast(
                            List[int],
                            kanienkeha_syllabify_word(
                                prepared_word, return_string=False
                            ),
                        )
                    else:
                        word_syllable_boundaries = cast(
                            List[int],
                            syllabify_word(prepared_word, return_string=False),
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
        syllabified_text.append(SyllabifiedTextSection(syllabified_section))
    logging.debug("Syllabified text: %s", ", ".join(str(s) for s in syllabified_text))
    return syllabified_text, spacing_adjusted


def flatten_syllabified_text(syllabified_text: List[SyllabifiedTextSection]) -> str:
    """
    Flattens a list of syllabified text sections to a string.

    syllabified_text [List[SyllabifiedTextSection]]: list of syllabified text sections

    returns [str]: flattened text string
    """
    return " ".join([s.flatten_to_str() for s in syllabified_text])
