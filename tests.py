import unittest

from latin_word_syllabification import syllabify_word
from syllabify import _clean_text, _prepare_text


class TestWordSyllabification(unittest.TestCase):
    def test_syllabify_word(self):
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
        }
        for word, expected in test_words.items():
            with self.subTest(word=word):
                self.assertEqual(syllabify_word(word, as_list=False), expected)


class TestTextSyllabification(unittest.TestCase):
    def test_clean_test(self):
        initial_text = "abcdefg @#$&*[^@]#${}|~[]\/|"
        expected_text = "abcdefg #[]#{}|~[]|"
        self.assertEqual(_clean_text(initial_text), expected_text)

    def test_prepare_text(self):
        initial_text = " abcdefg  {#} gau-[dia] | Alleluia "
        expected_text = "abcdefg gaudia alleluia"
        self.assertEqual(_prepare_text(initial_text), expected_text)
