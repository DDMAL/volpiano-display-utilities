# volpiano-display-utilities

This repository provides a set of modules for the syllabification of latin chant texts and the alignment of chant texts with volpiano according to the conventions of Cantus Database. 

The respository consists of three main utilities:
1. A tool (`cantus_text_syllabification.syllabify_text`) that parses text and syllabifies it for display with a melody. This tool assumes that input text conforms to Cantus Database specifications for text entry, including handling of incipits, text division, and missing text or music.
2. A tool (`latin_word_syllabification.syllabify_word`) that splits latin words into syllables based on linguistic rules. This tool could theoretically be used to syllabify latin words from any latin text, whether or not it is transcribed according to Cantus Database specifications. 
3. A tool (`text_volpiano_alignment.align_text_and_volpiano`) that aligns a chant's text and volpiano together for display in the browser. The tool includes basic handling of misalignments due to encoding error. 

### Text Syllabification

`syllabify_text` parses a chant text encoded to Cantus Database specifications for display with a melody. A brief overview of Cantus Database encoding conventions can be found below or at www.cantusdatabase.org/documents. 

```python
>>> from cantus_text_syllabification import syllabify_text
>>> syllabify_text("Angus dei qui {tollis peccata} mundi | Miserere # | ~Agnus")
'[[["Ag-","nus"], ["de-","i"], ["qui"]], [["{tollis peccata}"]], [["mun-","di"]], [["|"]], [["Mi-","se-","re-","re"], ["#"]], [["|"]], [["~Angus"]]]'
>>> syllabify_text("Glori@ patr1 &t")
'ValueError: ...' # Input with invalid characters will return a value error. 
```

Argument `flatten_result` modifies the function return value.

```python
>>> syllabify_text("Angus dei qui {tollis peccata} mundi | Miserere # | ~Agnus", flatten_result = True)
'Ag-nus de-i qui {tollis peccata} mun-di | Mi-se-re-re # | ~Angus'
```

The function returns a nested list of strings with the following structure:
 - each element of the list is a sublist that contains the syllabification of a section of the chant text. Sections are created when signaled in the chant text by pipes ("|") or when a substring of the chant text should not be syllabified (eg. when it corresponds to missing music -- these are detailed below)
 - each section list is a list of words (for sections where syllabification is necessary) or a singleton list for the whole section (for sections where syllabification is not necessary)
 - each word is a list of syllable strings (if the word needs to be syllabified)

 Consider the following example:

#### Text Syllabification Rules

Aligning chant texts with melodies requires most words in the chant to be syllabified; however, there are a number of cases in which subsets of chant texts are not syllabified: 
 1. Chant text is missing. Missing chant text is encoded with "#" and is aligned with volpiano but not syllabified.
 2. Music is missing. Text associated with missing music is enclosed within curly braces ("{" and "}"). It is aligned with a section of blank staff but is not syllabified.
 3. The chant text includes an incipits. Incipits are prefixed by a tilde ("~") and/or enclosed in square brackets ("[","]"). These are aligned with music for the incipt but are not syllabified. 

 More details about text entry in Cantus Database can be found at https://cantus.uwaterloo.ca/documents
### Latin Word Syllabification

`syllabify_word` syllabifies individual latin words according to linguistic rules. `syllabify_word` can either return a list of syllable boundaries or a string hyphenated at syllable boundaries. Strings passed to `syllabify_word` must contain only ASCII alphabetic characters; strings with other characters will raise a `ValueError`. 

```python 
>>> from latin_word_syllabification import syllabify_word
>>> syllabify_word("cantus")
'[3]' # Returns a list of index positions of syllable break
>>> syllabify_word("alleluia")
'[2,4,6]' 
>>> syllabify_word("alleluia", return_tring = True)
'al-le-lu-ia' # Return string hyphenated at internal syllable boundaries
>>> syllabify_word("qui")
'[]' # Single-syllable words return an empty list

>>> from latin_word_syllabification import split_word_by_syl_bounds
>>> split_word_by_syl_bounds("cantus", [3])
'can-tus' # split_word_by_syl_bounds is used internally to hyphenate the word by passed syllable boundaries
``` 

#### Latin Syllabification Rules


##### Contributors & References

Anna De Bakker (@annamorphism) and Geneviève Gates-Panneton (@joyfulgen) contributed to the testing and development of this utility.

The following resources were used to determine the syllabification rules outlined above:

 - Johnson, Kyle P., Patrick J. Burns, John Stewart, Todd Cook, Clément Besnier, and William J. B. Mattingly. "The Classical Language Toolkit: An NLP Framework for Pre-Modern Languages." In Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing: System Demonstrations, pp. 20-29. 2021. 10.18653/v1/2021.acl-demo.3
 - Meagan Ayer, Allen and Greenough’s New Latin Grammar for Schools and Colleges. Carlisle, Pennsylvania: Dickinson College Commentaries, 2014. https://dcc.dickinson.edu/grammar/latin/syllables. 
 - Wheelock, Frederic. Wheelock's Latin. ed. Richard LaFleur and Paul Comeau. www.wheelockslatin.com.
 - Fr. Matthew Spencer. Exsurge project. https://github.com/frmatthew. The latin syllabifier therein is available at www.marello.org/tools/syllabifier.

Fabian Weber developed the volpiano font at the University of Regensburg under the direction of Prof. David Hiley. More details about volpiano can be found at http://www.fawe.de/volpiano/. 

## Development

Utlities in this repository use python's `logging` package. These messages are logged at the `DEBUG` level. 

A constant dictionary of syllabification exceptions is defined in cantus_text_syllabification.py where keys are strings that receive a non-standard syllabification in Cantus Database text and values are the string hyphenated at "syllable breaks." For example, `euouae` is "syllabified" as `e-u-o-u-a-e`. 

### Testing

This utility includes a suite of tests that can be run using python's `unittest` framework. All tests can be found in the `test` directory in `tests/tests.py`.

Run all tests from the main repository directory with 

```python
>>> python3 -m unittest test.tests
```

For ease, certain test cases are stored in other files:

1. Word syllabification test cases are stored in `tests/word_syllabification_tests.csv`. Test cases for word syllabification can be added directly to this file. The test word should be entered in the first column and the expected syllabification (syllables divided by hyphens ("-")) in the second column.
2. Text-volpiano alignment test cases are stored in `tests/alignment_test_cases.json`. Additional alignment test cases can be added to this file. 

Visualization of volpiano-text alignment is useful to ensure that the expected results of tests are actually the desired visualization. After adding an alignment test case to `tests/alignment_test_cases.json`, run `tests/visualize_tests.py`. This script creates an html document, `tests/alignment_test_cases.html`, that can be opened in the browser to visualize the alignment test case. The volpiano font must be downloaded for the browser to render the volpiano in these test cases. To visualize, download the font from http://www.fawe.de/volpiano/volpiano51_web.zip and unzip to a subdirectory `tests/static` of the main respository directory.