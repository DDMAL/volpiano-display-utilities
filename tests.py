import unittest

from latin_word_syllabification import syllabify_word


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
