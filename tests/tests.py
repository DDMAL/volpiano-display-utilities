"""
Tests functioanlity of this package.
"""
import unittest
import json
import csv

from latin_word_syllabification import syllabify_word, split_word_by_syl_bounds
from cantus_text_syllabification import (
    _clean_text,
    _prepare_string_for_syllabification,
    _split_text_sections,
    syllabify_text,
    stringify_syllabified_text,
)
from text_volpiano_alignment import align_text_and_volpiano


class TestWordSyllabification(unittest.TestCase):
    """
    Tests functions in latin_text_syllabification.
    """

    def test_syllabify_word(self):
        """Tests syllabify_word."""
        # Read test words from csv file and get syllable boundaries.
        # ie. "Be-ne-dic-tus" -> [2, 4, 7]
        test_words = {}
        with open(
            "tests/word_syllabification_tests.csv", "r", encoding="utf-8-sig"
        ) as f:
            reader = csv.reader(f)
            for row in reader:
                word = row[0]
                syl_list = row[1].split("-")
                syl_bound = 0
                syl_bounds = []
                for syl in syl_list[:-1]:
                    syl_bound += len(syl)
                    syl_bounds.append(syl_bound)
                test_words[word] = syl_bounds
        for word, expected in test_words.items():
            with self.subTest(word=word):
                self.assertEqual(syllabify_word(word, return_string=False), expected)

    def test_split_word_by_syl_bounds(self):
        """
        Tests split_word_by_syl_bounds.

        Test 1, 2, and 2+ syllable words.
        """
        test_words = {"Benedictus": "Be-ne-dic-tus", "qui": "qui", "venit": "ve-nit"}
        word_syl_bounds = {"Benedictus": [2, 4, 7], "qui": [], "venit": [2]}
        for word, expected in test_words.items():
            with self.subTest(word=word):
                self.assertEqual(
                    "".join(split_word_by_syl_bounds(word, word_syl_bounds[word])),
                    expected,
                )


class TestCantusTextSyllabification(unittest.TestCase):
    """
    Tests functions in cantus_text_syllabification.
    """

    def test_clean_test(self):
        """Tests _clean_text."""
        initial_text = "abcdefg @#$&*[^@]#${}|~[]/|\\"
        expected_text = "abcdefg #[]#{}|~[]|"
        self.assertEqual(_clean_text(initial_text), expected_text)

    def test_prepare_string_for_syllabification(self):
        """Tests _prepare_string_for_syllabification."""
        str_hyphen_start = "-ABCDEFG"
        str_hyphen_end = "ABCDEFG-"
        self.assertEqual(
            _prepare_string_for_syllabification(str_hyphen_start),
            ("ABCDEFG", True, False),
        )
        self.assertEqual(
            _prepare_string_for_syllabification(str_hyphen_end),
            ("ABCDEFG", False, True),
        )

    def test_split_text_sections(self):
        """
        Tests _split_text_sections.

        Note: Sections are defined by pipes and curly braces.
        """
        start_str = "Benedictus | ~qui [venit in] | {nomine Domini} amen"
        sectioned = [
            "Benedictus",
            "|",
            "~qui [venit in]",
            "|",
            "{nomine Domini}",
            "amen",
        ]
        self.assertEqual(_split_text_sections(start_str), sectioned)

    def test_stringify_syllabified_text(self):
        """Tests stringify_syllabified_text."""
        syllabified_text = [[["Sanc-", "tus"], ["sanc-", "tus"], ["sanc-", "tus"]]]
        exp_result = "Sanc-tus sanc-tus sanc-tus"
        self.assertEqual(stringify_syllabified_text(syllabified_text), exp_result)

    def test_syllabify_text(self):
        """Tests syllabify_text. Constructs a test string with all possible cases."""

        # Full text of test:
        # "Sanctus sanctus sanctus # Sabaoth plen- # sunt # -li et {terra gloria} tua
        # Bene- {dictus} qui venit {#} no- {#} -ne {#} -omini
        # {cantic- #} {#} {# -ovum} quia mirabilia fecit | salvavit sibi dextera
        # eius et brachium sanctum eius | ~Gloria | ~Ipsum [Canticum]"
        normal_text = "Sanctus sanctus sanctus"
        exp_normal_text = [[["Sanc-", "tus"], ["sanc-", "tus"], ["sanc-", "tus"]]]
        missing_complete_words = "# Sabaoth"
        exp_missing_complete_words = [[["#"], ["Sa-", "ba-", "oth"]]]
        missing_partial_words = "plen- # sunt # -li"
        exp_missing_partial_words = [[["plen-"], ["#"], ["sunt"], ["#"], ["-li"]]]
        words_with_missing_music = "et {terra gloria} tua"
        exp_words_with_missing_music = [[["et"]], [["{terra gloria}"]], [["tu-", "a"]]]
        partial_words_with_missing_music = "Bene- {dictus} qui"
        exp_partial_words_with_missing_music = [
            [["Be-", "ne-"]],
            [["{dictus}"]],
            [["qui"]],
        ]
        missing_whole_words_and_music = "venit {#}"
        exp_missing_whole_words_and_music = [[["ve-", "nit"]], [["{#}"]]]
        missing_partial_words_and_music = "no- {#} -ne {#} -omini"
        exp_missing_partial_words_and_music = [
            [["no-"]],
            [["{#}"]],
            [["-ne"]],
            [["{#}"]],
            [["-o-", "mi-", "ni"]],
        ]
        partial_text_with_all_music_missing = "{cantic- #} {#} {# -ovum}"
        exp_partial_text_with_all_music_missing = [
            [
                ["{cantic- #} {#} {# -ovum}"],
            ]
        ]
        text_with_section_break = "quia mirabilia fecit | salvavit sibi dextera eius"
        exp_text_with_section_break = [
            [["qui-", "a"], ["mi-", "ra-", "bi-", "li-", "a"], ["fe-", "cit"]],
            [["|"]],
            [
                ["sal-", "va-", "vit"],
                ["si-", "bi"],
                ["dex-", "te-", "ra"],
                ["e-", "ius"],
            ],
        ]
        text_with_incipit = "et brachium sanctum eius | ~Gloria | ~Ipsum [Canticum]"
        exp_text_with_incipit = [
            [["et"], ["bra-", "chi-", "um"], ["sanc-", "tum"], ["e-", "ius"]],
            [["|"]],
            [["~Gloria"]],
            [["|"]],
            [["~Ipsum [Canticum]"]],
        ]
        all_test_strings = [
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
        full_expected_result = [
            exp_normal_text,
            exp_missing_complete_words,
            exp_missing_partial_words,
            exp_words_with_missing_music,
            exp_partial_words_with_missing_music,
            exp_missing_whole_words_and_music,
            exp_missing_partial_words_and_music,
            exp_partial_text_with_all_music_missing,
            exp_text_with_section_break,
            exp_text_with_incipit,
        ]
        for test_case_num in range(10):
            with self.subTest(test_case_num=test_case_num):
                self.assertEqual(
                    syllabify_text(all_test_strings[test_case_num]),
                    full_expected_result[test_case_num],
                )


class TestTextVolpianoAlignment(unittest.TestCase):
    """
    Tests functions for aligning text and volpiano in
    text_volpiano_alignment.py.
    """

    def test_align_text_volpiano(self):
        """
        Tests align_text_volpiano.
        """
        with open(
            "tests/alignment_test_cases.json", encoding="ascii"
        ) as test_case_json:
            test_cases = json.load(test_case_json)
        for test_case in test_cases:
            tupled_case = []
            for list_elem in test_case["expected_result"]:
                tupled_case.append(tuple(list_elem))
            test_case["expected_result"] = tupled_case
        for test_case in test_cases:
            with self.subTest(test_case["case_name"]):
                result = align_text_and_volpiano(
                    test_case["text_input"],
                    test_case["vol_input"],
                )
                self.assertEqual(result, test_case["expected_result"])