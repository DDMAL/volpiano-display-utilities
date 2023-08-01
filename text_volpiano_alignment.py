"""
Module for aligning text and volpiano.

Volpiano entry assumes use of CantusDB conventions.
"""
import re
from cantus_text_syllabification import syllabify_text
import logging
from itertools import zip_longest, takewhile

# A string containing all valid volpiano characters in Cantus
# Database. Used to check for invalid characters.
VALID_VOLPIANO_CHARS = "-19abcdefghijklmnopqrsyz)ABCDEFGHIJKLMNOPQRSYZ3467]"

def _preprocess_volpiano(volpiano_str: str) -> str:
    """ 
    Prepares volpiano string for alignment with text:
    - Checks for any invalid characters
    - Ensures proper spacing around barlines ("3" and "4") and missing
        music indicators ("6")
    - Ensure volpiano string has an ending barline ("3" or "4")


    volpiano_str [str]: volpiano string

    returns [str]: preprocessed volpiano string
    """
    processed_str = ""
    volpiano_str_len = len(volpiano_str)
    for i , char in enumerate(volpiano_str):
        # Check if char is valid
        if char not in VALID_VOLPIANO_CHARS:
            logging.debug("Removed invalid character in volpiano string.")
            continue
        # Check if char is a barline or missing music indicator and ensure
        # proper spacing
        if i != volpiano_str_len - 1 and char in ["3", "4", "6"]:
            while processed_str[-3:] != "---":
                processed_str += "-"
            processed_str += char
            for j in range(1,4):
                if volpiano_str[i+j] == "-":
                    continue
                processed_str += "-"*(4-j)
                break
            continue
        processed_str += char
    # Ensure volpiano string ends with a spaced barline
    if processed_str[-4:] not in ["---3", "---4"]:
        logging.debug("Adding barline to end of volpiano string.")
        processed_str = processed_str.rstrip("-") + "---3"
    logging.debug("Preprocessed volpiano string: %s", processed_str)
    return processed_str

def _postprocess_spacing(comb_text_and_vol: "list[tuple[str, str]]") -> "list[tuple[str, str]]":
    """
    Handle some special spacing requirements for optimal display
    of volpiano with chant text.

    Ensures that:
     - the length of missing music sections responds to the length of 
        the text associated with the section
    - where an aligned element with overhanging text is following by
        an aligned element with overhanging volpiano (or vice versa),
        the elements are re-aligned to match the complementary overhangs
        e.g.: "a-men a-men" & "1---f---g--f--g---3" is realigned to
              "a-men a-men" & "1---f--g---f--g---3"
    
    comb_text_and_vol [list[tuple[str, str]]]: list of tuples of text syllables and volpiano syllables
    """
    comb_text_and_vol_rev_spacing = []
    for i, (text_elem, vol_elem) in enumerate(comb_text_and_vol):
        if vol_elem[0] == "6":
            text_length = len(text_elem)
            if text_length > 10:
                vol_elem = "6---" + "---"*(text_length//3) + "6---"
        comb_text_and_vol_rev_spacing.append((text_elem, vol_elem))
    return comb_text_and_vol_rev_spacing

def _align_word(text_word:"list[str]", volpiano_word:str) -> "list[tuple[str, str]]":
    txt_word = text_word
    vol_syls = re.findall(r".*?-{2,3}", volpiano_word)
    if len(txt_word) > len(vol_syls):
        squashed_txt_word = txt_word[:len(vol_syls) - 1]
        squashed_txt_word.append("".join(txt_word[len(vol_syls) - 1:]))
        txt_word = squashed_txt_word
    comb_wrd = list(zip_longest(txt_word, vol_syls, fillvalue=""))
    return comb_wrd

def _align_section(text_section:"list[list[str]]", volpiano_section:str) -> "list[tuple[str, str]]":
    logging.debug("Aligning section: %s", text_section)
    logging.debug("Volpiano section: %s", volpiano_section)
    comb_section = []
    if volpiano_section.startswith('6'):
        comb_section.append((text_section[0][0], volpiano_section))
    elif text_section[0][0].startswith("~"):
        full_text = "".join([syl for word in text_section for syl in word])
        comb_section.append((full_text, volpiano_section))
    else:
        vol_words = re.findall(r".*?---", volpiano_section)
        for txt_word, vol_word in zip_longest(text_section, vol_words, fillvalue="--"):
            if txt_word == "--":
                txt_word = [""]
            comb_wrd = _align_word(txt_word, vol_word)
            comb_section.extend(comb_wrd)
    logging.debug("Aligned section: %s", comb_section)
    return comb_section

def _get_text_sections_for_alignment(syllabified_text: "list[list[str]]") -> "list[str]":
    text_sections = []
    section = []
    txt_wrd_iter = 0
    while txt_wrd_iter < len(syllabified_text):
        remaining_text = syllabified_text[txt_wrd_iter:]
        if remaining_text[0] == ["|"] or remaining_text[0][0].startswith("{"):
            text_sections.append([remaining_text[0]])
            txt_wrd_iter += 1
            remaining_text = remaining_text[1:]
        elif remaining_text[0][0].startswith("~"):
            if len(remaining_text) == 1:
                text_sections.append([remaining_text[0]])
                txt_wrd_iter += 1
                remaining_text = remaining_text[1:]
            elif remaining_text[1][0].startswith("["):
                text_sections.append([remaining_text[0], remaining_text[1]])
                txt_wrd_iter += 2
                remaining_text = remaining_text[2:]
            else:
                text_sections.append([remaining_text[0]])
                txt_wrd_iter += 1
                remaining_text = remaining_text[1:]
        section = list(takewhile(lambda x: x != ["|"] and not x[0].startswith("{"), remaining_text))
        if section:
            text_sections.append(section)
            txt_wrd_iter += len(section)
    return text_sections

def align_syllabified_text_and_volpiano(syllabified_text, volpiano_str):
    """
    Aligns syllabified text with volpiano, performing periodic sanity checks
    and accounting for misalignments.

    syllabified_text [list[list[str]]]: syllabified text
    volpiano_str [str]: volpiano string

    returns [list[tuple[str, str]]]: list of tuples of text syllables and volpiano syllables
    """
    volpiano_str = _preprocess_volpiano(volpiano_str)
    volpiano_sections = re.split(r"([134]-*|6-{6}6-{3})", volpiano_str)
    volpiano_sections = list(filter(lambda x: x != "", volpiano_sections))
    logging.debug("Volpiano sections: %s", volpiano_sections)
    text_sections = _get_text_sections_for_alignment(syllabified_text)
    logging.debug("Text sections: %s", text_sections)
    if len(volpiano_sections) == len(text_sections) + 2:
        comb_text_and_vol = [("", volpiano_sections[0])]
        for vol_sec, txt_sec in zip(volpiano_sections[1:-1], text_sections):
            aligned_section = _align_section(txt_sec, vol_sec)
            comb_text_and_vol.extend(aligned_section)
        comb_text_and_vol.append(("", volpiano_sections[-1]))
    comb_text_and_vol = _postprocess_spacing(comb_text_and_vol)
    logging.debug("Combined text and volpiano: %s", comb_text_and_vol)
    return comb_text_and_vol


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # VOLPIANO_TEST = "1---f---df--f--f---3---f--efgfe---4---g--hg-hgf--ef-gef--ed---3"
    # TEXT_TEST = "in diebus |eius | iustitia"
    # syllabified_text = syllabify_text(TEXT_TEST)
    # print(align_syllabified_text_and_volpiano(syllabified_text, VOLPIANO_TEST))
    VOLPIANO_TEST = "1---f---6------6---f--efgfe---g--hg-hgf---6------6---3"
    TEXT_TEST = (
        "in {#} eius obsess- {#}"
    )
    align_syllabified_text_and_volpiano(
        syllabify_text(TEXT_TEST), VOLPIANO_TEST
    )
