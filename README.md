# volpiano-display-utilities


## Chant Syllabification

Chant syllabification consists of two components:
1. A tool (`cantus_text_syllabification.syllabify_text`) that parses text and syllabifies it for display with a melody. This tool assumes that input text conforms to Cantus Database specifications for text entry, including handling of incipits, text division, and missing text or music.
2. A tool (`latin_word_syllabification.syllabify_word`) that splits latin words into syllables based on linguistic rules. This tool could theoretically be used to syllabify latin words from any latin text, whether or not it is transcribed according to Cantus Database specifications. 


### Text Syllabification

`syllabify_text` parses a chant text encoded to Cantus Database specifications for display with a melody. The function returns a list where each element corresponds to either: (a) a word, in which case it is a list of the word's syllables; or (b) some unit of text that according to specifications should not be syllabified, in which case it is a singleton list with the full text unit. 

```python
>>> from cantus_text_syllabification import syllabify_text
>>> syllabify_text("Angus dei qui {tollis peccata} mundi | Miserere # | ~Agnus")
'[["Ag-","nus"], ["de-","i"], ["qui"], ["{tollis peccata}"], ["mun-","di"], ["|"], ["Mi-","se-","re-","re"], ["#"], ["|"], ["~Angus"]]'
>>> syllabify_text("Glori@ patr1 &t")
'ValueError: ...' # Input with invalid characters will return a value error. 
```

Arguments `stringify_result` and `flatten_result` modify the function return value:

```python
>>> syllabify_text("Angus dei qui {tollis peccata} mundi | Miserere # | ~Agnus", stringify_result = True)
'Ag-nus de-i qui {tollis peccata} mun-di | Mi-se-re-re # | ~Angus'
>>> syllabify_text("Angus dei qui {tollis peccata} mundi | Miserere # | ~Agnus", flatten_result = True)
'["Ag-","nus", "de-","i", "qui", "{tollis peccata}", "mun-","di", "|", "Mi-","se-","re-","re", "#", "|", "~Angus"]'
```

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
>>> syllabify_word("alleluia", return_syllabified_string = True)
'al-le-lu-ia' # Return string hyphenated at internal syllable boundaries
>>> syllabify_word("qui")
'[]' # Single-syllable words return an empty list

>>> from latin_word_syllabification import split_word_by_syl_bounds
>>> split_word_by_syl_bounds("cantus", [3])
'can-tus' # split_word_by_syl_bounds is used internally to hyphenate the word by passed syllable boundaries
``` 

#### Latin Syllabification Rules


##### References

The following resources were used to determine the syllabification rules outlined above:

 - Johnson, Kyle P., Patrick J. Burns, John Stewart, Todd Cook, Clément Besnier, and William J. B. Mattingly. "The Classical Language Toolkit: An NLP Framework for Pre-Modern Languages." In Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing: System Demonstrations, pp. 20-29. 2021. 10.18653/v1/2021.acl-demo.3
 - Meagan Ayer, Allen and Greenough’s New Latin Grammar for Schools and Colleges. Carlisle, Pennsylvania: Dickinson College Commentaries, 2014. https://dcc.dickinson.edu/grammar/latin/syllables. 
 - Wheelock, Frederic. Wheelock's Latin. ed. Richard LaFleur and Paul Comeau. www.wheelockslatin.com.
 - Fr. Matthew Spencer. Exsurge project. https://github.com/frmatthew. The latin syllabifier therein is available at www.marello.org/tools/syllabifier.


## Details for Development

Utlities in this repository use python's `logging` package. These messages are logged at the `DEBUG` level. 

Tests are constructed using python's `unittest` framework. Run all tests with `python -m unittest tests.py`.

A constant dictionary of syllabification exceptions is defined in cantus_text_syllabification.py where keys are strings that receive a non-standard syllabification in Cantus Database text and values are the string hyphenated at "syllable breaks." For example, `euouae` is "syllabified" as `e-u-o-u-a-e`. 