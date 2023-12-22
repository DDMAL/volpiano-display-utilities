"""
Defines the SyllabifiedSection class and subclasses for syllabified text and
volpiano. SyllabifiedSection objects are used to store syllabified text and
volpiano and the provide methods useful for the alignment process. 
"""

from typing import List


class SyllabifiedSection:
    """
    Base class for SyllabifiedTextSection and SyllabifiedVolpianoSection.
    """

    def __init__(self, section: List[List[str]]):
        self.section = section

    def __str__(self):
        return str(self.section)

    @property
    def num_words(self) -> int:
        """
        Returns the number of words in the section.
        """
        return len(self.section)

    def get_syllable(self, word_num: int, syllable_num: int) -> str:
        """
        Returns the syllable of the section with the given syllable number.
        """
        return self.section[word_num][syllable_num]


class SyllabifiedTextSection(SyllabifiedSection):
    """
    Class containing a syllabified section of text. The section attribute is a
    list of lists of strings: each element of the outer list is a word, and each
    element of the inner list is a syllable of that word.

    A list of these classes (one for each section of text) is returned by the
    cantus_text_syllabification.syllabify_text() function.
    """

    @property
    def is_syllabified(self) -> bool:
        """
        Returns True if the section is syllabified.
        """
        return (
            not self.section[0][0].startswith("~")
            and not self.section[0][0].startswith("[")
            and not self.section[0][0].startswith("{")
            and not self.section[0][0][0] == "|"
        )

    @property
    def is_barline(self) -> bool:
        """
        Returns True if the section is a section endcoding a barline.
        """
        return self.section[0][0][0] == "|"


class SyllabifiedVolpianoSection(SyllabifiedSection):
    """
    Class containing a syllabified section of volpiano. The section attribute is
    a list of lists of strings: each element of the outer list is a word, and
    each element of the inner list is a syllable of that word.

    A list of these classes (one for each section of volpiano) is returned by
    volpiano_syllabification.syllabify_volpiano() function.
    """

    @property
    def is_barline(self) -> bool:
        """
        Returns True if the section is a section endcoding a barline.
        """
        return self.section[0][0][0] == "3" or self.section[0][0][0] == "4"

    @property
    def is_missing_music(self) -> bool:
        """
        Returns True if the section is section encoding missing music.
        """
        return self.section[0][0].startswith("6")

    def flatten_to_str(self) -> str:
        """
        Flattens the syllabified section of volpiano into a string.

        returns [str]: flattened volpiano string.
        """
        # First combine syllables into words.
        word_list: List[str] = []
        for word in self.section:
            word_list.append("".join(word))
        # Then join words with the word separator.
        flattened_section: str = "".join(word_list)
        return flattened_section
