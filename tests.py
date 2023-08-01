"""
Tests functioanlity of this package.
"""
import unittest
import json

from latin_word_syllabification import syllabify_word, split_word_by_syl_bounds
from cantus_text_syllabification import (
    _clean_text,
    _prepare_string_for_syllabification,
    _get_text_sections,
    syllabify_text,
    stringify_syllabified_text,
    flatten_syllabified_text,
)
from text_volpiano_alignment import align_syllabified_text_and_volpiano

class TestWordSyllabification(unittest.TestCase):
    """
    Tests functions in latin_text_syllabification.
    """

    def test_split_word_by_syl_bounds(self):
        """Tests split_word_by_syl_bounds."""
        test_words = {
            "Benedictus": "Be-ne-dic-tus",
            "qui": "qui",
            "venit": "ve-nit",
            "illuxit": "il-lux-it",
            "caelum": "cae-lum",
            "heriles": "he-ri-les",
            "dei": "de-i",
            "gaudia": "gau-di-a",
            "foenum": "foe-num",
            "aetheris": "ae-the-ris",
            "aquarum": "a-qua-rum",
            "cuius": "cu-ius",
            "alleluia": "al-le-lu-ia",
            "alleluya": "al-le-lu-ya",
            "hierusalem": "hie-ru-sa-lem",
            "ihesum": "ihe-sum",
            "adiuvabit": "ad-iu-va-bit",
            "mihi": "mi-hi",
        }
        word_syl_bounds = {
            "Benedictus": [2, 4, 7],
            "qui": [],
            "venit": [2],
            "illuxit": [2, 5],
            "caelum": [3],
            "heriles": [2, 4],
            "dei": [2],
            "gaudia": [3, 5],
            "foenum": [3],
            "aetheris": [2, 5],
            "aquarum": [1, 4],
            "cuius": [2],
            "alleluia": [2, 4, 6],
            "alleluya": [2, 4, 6],
            "hierusalem": [3, 5, 7],
            "ihesum": [3],
            "adiuvabit": [2, 4, 6],
            "mihi": [2],
        }
        for word, expected in test_words.items():
            with self.subTest(word=word):
                self.assertEqual(
                    "".join(split_word_by_syl_bounds(word, word_syl_bounds[word])),
                    expected,
                )

    def test_syllabify_word(self):
        """Tests syllabify_word."""
        test_words = {
            "Benedictus": [2, 4, 7],
            "qui": [],
            "venit": [2],
            "illuxit": [2, 5],
            "caelum": [3],
            "heriles": [2, 4],
            "dei": [2],
            "gaudia": [3, 5],
            "foenum": [3],
            "aetheris": [2, 5],
            "aquarum": [1, 4],
            "cuius": [2],
            "alleluia": [2, 4, 6],
            "alleluya": [2, 4, 6],
            "hierusalem": [3, 5, 7],
            "ihesum": [3],
            "adiuvabit": [2, 4, 6],
            "mihi": [2],
            "levavi": [2,4],
            "leuaui": [2,4],
            "uniuersi": [1,3,6],
            "labijs": [2,4],
            "labiis": [2,4],
            "filij": [2,4],
            "filii": [2,4],
            "subiit": [3,4],
            "israel": [2,4],
            "michael": [2,5],
        }
        for word, expected in test_words.items():
            with self.subTest(word=word):
                self.assertEqual(
                    syllabify_word(word, return_syllabified_string=False), expected
                )


class TestCantusTextSyllabification(unittest.TestCase):
    """
    Tests functions in cantus_text_syllabification.
    """

    def test_clean_test(self):
        """Tests _clean_text."""
        initial_text = "abcdefg @#$&*[^@]#${}|~[]\/|"
        expected_text = "abcdefg #[]#{}|~[]|"
        self.assertEqual(_clean_text(initial_text), expected_text)

    def test_prepare_string_for_syllabification(self):
        """Tests _prepare_string_for_syllabification."""
        str_hyphen_start = "-ABCDEFG"
        str_hyphen_end = "ABCDEFG-"
        str_no_hyphen = "ABCDEFG"
        self.assertEqual(
            _prepare_string_for_syllabification(str_hyphen_start),
            ("abcdefg", True, False),
        )
        self.assertEqual(
            _prepare_string_for_syllabification(str_hyphen_end),
            ("abcdefg", False, True),
        )
        self.assertEqual(
            _prepare_string_for_syllabification(str_no_hyphen),
            ("abcdefg", False, False),
        )

    def test_get_text_sections(self):
        """
        Tests _get_text_sections.

        Note: Sections are defined by pipes, curly braces, and square brackets.
        """
        start_str = "Benedictus | qui [venit] in | {nomine Domini} amen"
        sectioned = [
            "Benedictus ",
            "|",
            " qui ",
            "[venit]",
            " in ",
            "|",
            " ",
            "{nomine Domini}",
            " amen",
        ]
        self.assertEqual(_get_text_sections(start_str), sectioned)

    def test_stringify_syllabified_text(self):
        """Tests stringify_syllabified_text."""
        syllabified_text = [["San-", "ctus"], ["san-", "ctus"], ["san-", "ctus"]]
        exp_result = "San-ctus san-ctus san-ctus"
        self.assertEqual(stringify_syllabified_text(syllabified_text), exp_result)

    def test_flatten_syllabified_text(self):
        """Tests flatten_syllabified_text."""
        syllabified_text = [["San-", "ctus"], ["san-", "ctus"], ["san-", "ctus"]]
        exp_result = ["San-", "ctus", "san-", "ctus", "san-", "ctus"]
        self.assertEqual(flatten_syllabified_text(syllabified_text), exp_result)

    def test_syllabify_text(self):
        """Tests syllabify_text. Constructs a test string with all possible cases."""
        normal_text = "Sanctus sanctus sanctus"
        exp_normal_text = [["San-", "ctus"], ["san-", "ctus"], ["san-", "ctus"]]
        missing_complete_words = "# Sabaoth"
        exp_missing_complete_words = [["#"], ["Sa-", "ba-", "oth"]]
        missing_partial_words = "plen- # sunt # -li"
        exp_missing_partial_words = [["plen-"], ["#"], ["sunt"], ["#"], ["-li"]]
        words_with_missing_music = "et {terra gloria} tua"
        exp_words_with_missing_music = [["et"], ["{terra gloria}"], ["tu-", "a"]]
        partial_words_with_missing_music = "Bene- {dictus} qui"
        exp_partial_words_with_missing_music = [["Be-", "ne-"], ["{dictus}"], ["qui"]]
        missing_whole_words_and_music = "venit {#}"
        exp_missing_whole_words_and_music = [["ve-", "nit"], ["{#}"]]
        missing_partial_words_and_music = "no- {#} -ne {#} -omini"
        exp_missing_partial_words_and_music = [
            ["no-"],
            ["{#}"],
            ["-ne"],
            ["{#}"],
            ["-o-", "mi-", "ni"],
        ]
        partial_text_with_all_music_missing = "{cantic- #} {#} {# -ovum}"
        exp_partial_text_with_all_music_missing = [
            ["{cantic- #}"],
            ["{#}"],
            ["{# -ovum}"],
        ]
        text_with_section_break = "quia mirabilia fecit | salvavit sibi dextera eius"
        exp_text_with_section_break = [
            ["qui-", "a"],
            ["mi-", "ra-", "bi-", "li-", "a"],
            ["fe-", "cit"],
            ["|"],
            ["sal-", "va-", "vit"],
            ["si-", "bi"],
            ["dex-", "te-", "ra"],
            ["e-", "ius"],
        ]
        text_with_incipit = "et brachium sanctum eius | ~Gloria | ~Ipsum [Canticum]"
        exp_text_with_incipit = [
            ["et"],
            ["bra-", "chi-", "um"],
            ["san-", "ctum"],
            ["e-", "ius"],
            ["|"],
            ["~Gloria"],
            ["|"],
            ["~Ipsum"],
            ["[Canticum]"],
        ]
        cantusdb_syllabification_exceptions = {
            "euouae": ["e-", "u-", "o-", "u-", "a-", "e"]
        }
        # Full text of test string:
        # "Sanctus sanctus sanctus # Sabaoth plen- # sunt # -li et {terra gloria} tua Bene- {dictus} qui venit {#} no- {#} -ne {#} -omini
        # {cantic- #} {#} {# -ovum} quia mirabilia fecit | salvavit sibi dextera eius et brachium sanctum eius | ~Gloria | ~Ipsum [Canticum]"
        # + all cantus syllabification_exceptions
        full_test_string = " ".join(
            [
                normal_text,
                missing_complete_words,
                missing_partial_words,
                words_with_missing_music,
                partial_words_with_missing_music,
                missing_whole_words_and_music,
                missing_partial_words_and_music,
                partial_text_with_all_music_missing,
                text_with_section_break,
                text_with_incipit,
            ]
            + list(cantusdb_syllabification_exceptions.keys())
        )
        full_expected_result = (
            exp_normal_text
            + exp_missing_complete_words
            + exp_missing_partial_words
            + exp_words_with_missing_music
            + exp_partial_words_with_missing_music
            + exp_missing_whole_words_and_music
            + exp_missing_partial_words_and_music
            + exp_partial_text_with_all_music_missing
            + exp_text_with_section_break
            + exp_text_with_incipit
            + list(cantusdb_syllabification_exceptions.values())
        )
        syllabified_text = syllabify_text(full_test_string)
        self.assertEqual(syllabified_text, full_expected_result)


class TestTextVolpianoAlignment(unittest.TestCase):
    """
    Tests functions for aligning text and volpiano in
    text_volpiano_alignment.py.
    """

    def test_align_text_volpiano(self):
        """
        Tests align_text_volpiano.
        """
        with open("alignment_test_cases.json", encoding="ascii") as test_case_json:
            test_cases = json.load(test_case_json)
        for test_case in test_cases:
            tupled_case = []
            for list_elem in test_case["expected_result"]:
                tupled_case.append(tuple(list_elem))
            test_case["expected_result"] = tupled_case
        for test_case in test_cases:
            with self.subTest(test_case["case_name"]):
                result = align_syllabified_text_and_volpiano(
                    syllabify_text(test_case["text_input"]),
                    test_case["vol_input"],
                )
                self.assertEqual(result, test_case["expected_result"])
