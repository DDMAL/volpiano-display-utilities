from typing import List

class SyllabifiedSection:
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
        # First combine syllables into words.
        word_list: List[str] = []
        for word in self.section:
            word_list.append("".join(word))
        # Then join words with the word separator.
        flattened_section: str = "".join(word_list)
        return flattened_section
