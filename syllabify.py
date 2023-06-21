import re

from latin_word_syllabification import syllabify_word


def _clean_text(test: str) -> str:
    """
    Removes invalid characters from the text string.

    test [str]: string to clean

    returns [str]: cleaned string
    """
    return re.sub(r"[^a-zA-Z#~\{\}\[\]\|\- ]", "", test)


def _prepare_text(text: str) -> str:
    """
    Complete preparation of the text string before syllabification.
    Cleaning:
        - makes all characters lowercase
        - removes all non-alphabetic (but still valid) characters (eg.
            "#", brackets, etc.)
        - replaces all runs of consecutive spaces to single spaces
        - removes leading and trailing whitespace

    text [str]: string to clean

    returns [str]: cleaned string
    """
    text = re.sub(r"[#~\{\}\[\]\|\-]", "", text)
    text = re.sub(r" +", " ", text)
    text = text.strip()
    text = text.lower()
    return text
