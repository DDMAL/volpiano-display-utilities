"""
Tests functioanlity of this package.
"""
import unittest
import json
import csv

from volpiano_display_utilities.latin_word_syllabification import (
    syllabify_word,
    split_word_by_syl_bounds,
)
from volpiano_display_utilities.cantus_text_syllabification import (
    _clean_text,
    _prepare_string_for_syllabification,
    _split_text_sections,
    syllabify_text,
    flatten_syllabified_text,
)
from volpiano_display_utilities.volpiano_syllabification import (
    prepare_volpiano_for_syllabification,
    syllabify_volpiano,
    adjust_missing_music_spacing_for_rendering,
)
from volpiano_display_utilities.text_volpiano_alignment import align_text_and_volpiano


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

    def test_cantus_exceptions(self):
        """Tests syllabification of a few words that are exceptions
        in the Cantus Database."""
        exception_word = "euouae"
        syllabified_word = flatten_syllabified_text(syllabify_text(exception_word))
        self.assertEqual(syllabified_word, "e-u-o-u-a-e")
        exception_word_capitalized = "Euouae"
        syllabified_word_capitalized = flatten_syllabified_text(
            syllabify_text(exception_word_capitalized)
        )
        self.assertEqual(syllabified_word_capitalized, "E-u-o-u-a-e")

    def test_clean_text(self):
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

    def test_syllabify_text(self):
        """Tests syllabify_text. Constructs a test string with all possible cases."""

        # Full text of test:
        # "Sanctus sanctus sanctus # Sabaoth plen- # sunt # -li et {terra gloria} tua
        # Bene- {dictus} qui venit {#} no- {#} -ne {#} -omini
        # {cantic- #} {#} {# -ovum} quia mirabilia fecit | salvavit sibi dextera
        # eius et brachium sanctum eius | ~Gloria | ~Ipsum [Canticum]"
        test_cases = [
            {
                "case_name": "Normal Text",
                "test_string": "Sanctus sanctus sanctus",
                "expected_result": [
                    [["Sanc-", "tus"], ["sanc-", "tus"], ["sanc-", "tus"]]
                ],
            },
            {
                "case_name": "Missing Complete Words",
                "test_string": "# Sabaoth",
                "expected_result": [[["#"], ["Sa-", "ba-", "oth"]]],
            },
            {
                "case_name": "Missing Partial Words",
                "test_string": "plen- # sunt # -li",
                "expected_result": [[["plen-"], ["#"], ["sunt"], ["#"], ["-li"]]],
            },
            {
                "case_name": "Words with Missing Music",
                "test_string": "et {terra gloria} tua",
                "expected_result": [[["et"]], [["{terra gloria}"]], [["tu-", "a"]]],
            },
            {
                "case_name": "Partial Words with Missing Music",
                "test_string": "Bene- {dictus} qui",
                "expected_result": [[["Be-", "ne-"]], [["{dictus}"]], [["qui"]]],
            },
            {
                "case_name": "Missing Whole Words and Music",
                "test_string": "venit {#}",
                "expected_result": [[["ve-", "nit"]], [["{#}"]]],
            },
            {
                "case_name": "Missing Partial Words and Music",
                "test_string": "no- {#} -ne {#} -omini",
                "expected_result": [
                    [["no-"]],
                    [["{#}"]],
                    [["-ne"]],
                    [["{#}"]],
                    [["-o-", "mi-", "ni"]],
                ],
            },
            {
                "case_name": "Partial Text with All Music Missing",
                "test_string": "{cantic- #} {#} {# -ovum}",
                "expected_result": [[["{cantic- #}"]], [["{#}"]], [["{# -ovum}"]]],
            },
            {
                "case_name": "Text with Section Break",
                "test_string": "quia mirabilia fecit | salvavit sibi dextera eius",
                "expected_result": [
                    [["qui-", "a"], ["mi-", "ra-", "bi-", "li-", "a"], ["fe-", "cit"]],
                    [["|"]],
                    [
                        ["sal-", "va-", "vit"],
                        ["si-", "bi"],
                        ["dex-", "te-", "ra"],
                        ["e-", "ius"],
                    ],
                ],
            },
            {
                "case_name": "Text with Incipit",
                "test_string": "et brachium sanctum eius | ~Gloria | ~Ipsum [Canticum]",
                "expected_result": [
                    [["et"], ["bra-", "chi-", "um"], ["sanc-", "tum"], ["e-", "ius"]],
                    [["|"]],
                    [["~Gloria"]],
                    [["|"]],
                    [["~Ipsum [Canticum]"]],
                ],
            },
            {
                "case_name": "Text with incipit in middle of section",
                "test_string": "et brachium ~sanctum eius | Gloria ~canticum novum",
                "expected_result": [
                    [["et"], ["bra-", "chi-", "um"]],
                    [["~sanctum eius"]],
                    [["|"]],
                    [["Glo-", "ri-", "a"]],
                    [["~canticum novum"]],
                ],
            },
        ]
        for test_case in test_cases:
            with self.subTest(test_case["case_name"]):
                syllabified_text = syllabify_text(test_case["test_string"])
                syllabified_text_list = [
                    section.section for section in syllabified_text
                ]
                self.assertEqual(
                    syllabified_text_list,
                    test_case["expected_result"],
                )
        # Test presyllabified text
        presyllabified_text = (
            # Test case where a syllable break has been added
            # to where it might "normally" occur.
            "Ma-g-ni-fi-cat a-ni-ma me-a do-mi-nu-m | et "
            # Test missing music case
            "ex-ul-ta-vit {spi-ri-tus meus} in de-o | "
            # Test incipit case
            "{sa-lu-ta-ri} me-o | ~Quia [re-spex-it] | "
            # Test missing words and missing words + music case
            "# hu-mi-li- # # -lae su- {#} "
            # Test case where we might expect a syllable break, but
            # user has removed syllable break.
            "| ecce enim ex hoc be-a-tam"
        )
        expected_result = [
            [
                ["Ma-", "g-", "ni-", "fi-", "cat"],
                ["a-", "ni-", "ma"],
                ["me-", "a"],
                ["do-", "mi-", "nu-", "m"],
            ],
            [["|"]],
            [["et"], ["ex-", "ul-", "ta-", "vit"]],
            [["{spi-ri-tus meus}"]],
            [["in"], ["de-", "o"]],
            [["|"]],
            [["{sa-lu-ta-ri}"]],
            [["me-", "o"]],
            [["|"]],
            [["~Quia [re-spex-it]"]],
            [["|"]],
            [["#"], ["hu-", "mi-", "li-"], ["#"], ["#"], ["-lae"], ["su-"]],
            [["{#}"]],
            [["|"]],
            [["ecce"], ["enim"], ["ex"], ["hoc"], ["be-", "a-", "tam"]],
        ]
        with self.subTest("Presyllabified Text"):
            syllabified_text = syllabify_text(
                presyllabified_text, text_presyllabified=True
            )
            syllabified_text_list = [section.section for section in syllabified_text]
            self.assertEqual(
                syllabified_text_list,
                expected_result,
            )


class TestVolpianoSyllabification(unittest.TestCase):
    """
    Tests functions for syllabifying volpiano in volpiano_syllabification.py.
    """

    def test_prepare_volpiano_for_alignment(self):
        standard_volpiano = "1---g---h---3"
        volpiano_with_extra_starting_matter = "tf-g-1---g-1--h---3"
        expected = "g---h---3"
        with self.subTest("Standard starting material"):
            (
                prepared_volpiano,
                vol_chars_rmvd_flag,
            ) = prepare_volpiano_for_syllabification(standard_volpiano)
            self.assertEqual(prepared_volpiano, expected)
            self.assertFalse(vol_chars_rmvd_flag)
        with self.subTest("Extra starting material"):
            (
                prepared_volpiano,
                vol_chars_rmvd_flag,
            ) = prepare_volpiano_for_syllabification(
                volpiano_with_extra_starting_matter
            )
            self.assertEqual(
                prepared_volpiano,
                expected,
            )
            self.assertTrue(vol_chars_rmvd_flag)

    def test_syllabify_volpiano(self):
        volpiano_syllabification_test_cases = [
            {
                "case_name": "Section divided by barline '3' + standard spacing",
                "volpiano": "a-b--c---d---e---3---",
                "vol_improperly_encoded": False,
                "expected_result": [
                    [["a-b--", "c---"], ["d---"], ["e---"]],
                    [["3---"]],
                ],
            },
            {
                "case_name": "Section divided by barline '4' + standard spacing",
                "volpiano": "a-b--c---d---e---4---",
                "vol_improperly_encoded": False,
                "expected_result": [
                    [["a-b--", "c---"], ["d---"], ["e---"]],
                    [["4---"]],
                ],
            },
            {
                "case_name": "Section divided by barline '3' + non-standard spacing",
                "volpiano": "a-b--c---d---e-3--",
                "vol_improperly_encoded": True,  # There should be 3 hyphens both before and after barline
                "expected_result": [[["a-b--", "c---"], ["d---"], ["e-"]], [["3--"]]],
            },
            {
                "case_name": "Section divided by barline '4' + break encoded",
                "volpiano": "a-b--c---d---e---47---",
                "vol_improperly_encoded": False,
                "expected_result": [
                    [["a-b--", "c---"], ["d---"], ["e---"]],
                    [["47---"]],
                ],
            },
            {
                "case_name": "Missing music section",
                "volpiano": "a-b--c---6------6---",
                "vol_improperly_encoded": False,
                "expected_result": [[["a-b--", "c---"]], [["6------6---"]]],
            },
            {
                "case_name": "Missing music section with break encoded",
                "volpiano": "a-b--c---6------6---77",
                "vol_improperly_encoded": True,  # Section break marks should immediately follow "6"
                "expected_result": [[["a-b--", "c---"]], [["6------6---77"]]],
            },
        ]
        for test_case in volpiano_syllabification_test_cases:
            with self.subTest(test_case["case_name"]):
                syllabified_volpiano, vol_improperly_encoded = syllabify_volpiano(
                    test_case["volpiano"]
                )
                syllabified_volpiano_list = [
                    section.section for section in syllabified_volpiano
                ]
                self.assertEqual(
                    syllabified_volpiano_list,
                    test_case["expected_result"],
                )
                self.assertEqual(
                    vol_improperly_encoded, test_case["vol_improperly_encoded"]
                )

    def test_adjust_missing_music_spacing_for_rendering(self):
        with self.subTest("Not a missing music section"):
            volpiano = "a-b--c---"
            text_length = 3
            self.assertRaises(
                ValueError,
                adjust_missing_music_spacing_for_rendering,
                volpiano,
                text_length,
            )
        with self.subTest("Missing music with fewer than 10 chars"):
            volpiano = "6------6---"
            text_length = 4
            expected = "6------6---"
            self.assertEqual(
                adjust_missing_music_spacing_for_rendering(volpiano, text_length),
                expected,
            )
        with self.subTest("Missing music with more than 10 chars"):
            volpiano = "6------6---"
            text_length = 14
            expected = "6--------------6---"
            self.assertEqual(
                adjust_missing_music_spacing_for_rendering(volpiano, text_length),
                expected,
            )
        with self.subTest("Missing music with break encoded"):
            volpiano = "6------677---"
            text_length = 8
            expected = "6------677---"
            self.assertEqual(
                adjust_missing_music_spacing_for_rendering(volpiano, text_length),
                expected,
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
        # We have to convert the expected results from a list of lists to a list
        # of tuples, because the expected results of align_text_and_volpiano are
        # lists of tuples.
        for test_case in test_cases:
            tupled_case = []
            for list_elem in test_case["expected_result"]:
                tupled_case.append(tuple(list_elem))
            test_case["expected_result"] = tupled_case
        for test_case in test_cases:
            with self.subTest(test_case["case_name"]):
                result, review_encoding_flag = align_text_and_volpiano(
                    test_case["text_input"], test_case["vol_input"]
                )
                self.assertEqual(result, test_case["expected_result"])
                self.assertEqual(
                    review_encoding_flag, test_case["review_encoding_flag"]
                )
