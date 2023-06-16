"""
A utility to syllabify strings of Latin text stored in
CantusDB. As a result, this utility assumes latin transcription
conventions of CantusDB (found in the "Text Entry and Editing" pdf
at https://cantus.uwaterloo.ca/documents) which include both standardized
classical latin spelling and non-standardized (ie. what is 
actually in the manuscript) spellings. Consult the README for more
details.

Use syllabify_text method to syllabify a string.

syllabify_test(text, verbose=False)
    text [str]: string to syllabify
    verbose [bool]: print debug info

returns a list of syllables with syllable boundaries marked by hyphens.
"""

import re
import logging

_CONSONANT_GROUPS = [
    "qu",
    "ch",
    "ph",
    "fl",
    "fr",
    "st",
    "br",
    "cr",
    "cl",
    "pr",
    "tr",
    "ct",
    "th",
    "sp",
]
_DIPTHONGS = [
    "ae",
    "au",
    "ei",
    "oe",
    "ui",
    "ya",
    "ex",
    "ix",
    "ihe",  # ihe-sus, ihe-ru-sa-lem
]
_VOWELS = [
    "a",
    "e",
    "i",
    "o",
    "u",
    "y",
]

# add uppercase variants of every single symbol.
consonant_groups += [x[0].upper() + x[1:] for x in consonant_groups]
diphthongs += [x[0].upper() + x[1:] for x in diphthongs]
vowels += [x[0].upper() + x[1:] for x in vowels]


def clean_transcript(text: str) -> str:
    """
    Complete preparatory cleaning of the text string before syllabification.
    Cleaning:
        - makes all characters lowercase
        - removes all non-whitespace and all non-unicode characters
        - removes all vertical bars
        - replaces all runs of consecutive spaces to single spaces
        - removes leading and trailing whitespace

    text [str]: string to clean

    returns [str]: cleaned string
    """
    text = re.sub(r"[^\s\w]", "", text)
    text = re.sub(r" \| ", " ", text)
    text = re.sub(r" +", " ", text)
    text = text.strip()
    text = text.lower()
    return text

def _is_vowel(char: str) -> bool:
    """
    Checks if a character is a vowel.

    char [str]: character to check

    returns [bool]: True if char is a vowel, False otherwise
    """
    return char in _VOWELS

def _get_vowel_group(word:str, word_indexer:int) -> str:
    """
    Gets the entire vowel group starting at specific index.

    word [str]: word to get vowel group from
    word_indexer [int]: index of first vowel in vowel group

    returns [str]: vowel group
    """
    # Start vowel group with identified vowel
    vowel_group = word[word_indexer]
    # If at the end of the word, return the vowel.
    if word_indexer == len(word) - 1:
        return vowel_group
    # If the following letter is not a vowel, return the single vowel.
    if not _is_vowel(word[word_indexer + 1]):
        return vowel_group
    # If following letter is a vowel, the two vowels should either be 
    # an expected dipthong or should be part of a construction
    # vowel + i + vowel. If a dipthong, return the dipthong. If vowel + i + vowel,
    # return the first vowel (i is a consonant in this case).
    if word[word_indexer:word_indexer + 2] in _DIPTHONGS:
        return word[word_indexer:word_indexer + 2]
    return vowel_group

def _get_syllable_ending(word: str, word_indexer: int) -> str:
    """
    Gets the end of a syllable starting at specific index.

    word [str]: word to check
    word_indexer [int]: index of current letter in word

    returns [str]: The string that terminates the syllable
    """
    

def _syllabify_word(word: str, verbose: bool = False) -> "list[str]":
    """
    Separates words into syllables. See README for details on syllabification rules.

    word [str]: word to syllabify
    verbose [bool]: print debug information

    returns [list[str]]: list of syllables
    """
    if verbose:
        logging.debug("Syllabifying word: %s", word)

    if len(word) <= 1:
        return [word]

    syls_list = []
    word_indexer = 0
    syl = ""
    while word_indexer < len(word):
        # Check if current letter is a vowel. 
        # If not, add to the syllable and continue.
        # If so, this signals the start of a vowel group and
        # we pass the word to _get_vowel_group to obtain the 
        # entire vowel group.
        if not _is_vowel(word[word_indexer]):
            syl += word[word_indexer]
            word_indexer += 1
            continue
        vowel_group:str = _get_vowel_group(word, word_indexer)
        syl += vowel_group
        word_indexer += len(vowel_group)
        # Once a vowel group has been found, the syllable can
        # be terminated and added to the list of syllables.
        syllable_ending = _get_syllable_ending(word, word_indexer)
        syl += syllable_ending
        word_indexer += len(syllable_ending)
        # If this is not the end of the word, add a hyphen to the
        # syllable.
        if word_indexer < len(word) - 1:
            syl += "-"
        syls_list.append(syl)
    return syls_list



    

def syllabify_word(inp, verbose=False):
    """
    separate each word into UNITS - first isolate consonant groups, then diphthongs, then letters.
    each vowel / diphthong unit is a "seed" of a syllable; consonants and consonant groups "stick"
    to adjacent seeds. first make every vowel stick to its preceding consonant group. any remaining
    consonant groups stick to the vowel behind them.
    """
    #

    # remove all whitespace and newlines from input:
    inp = re.sub(r"[\s+]", "", inp)

    # convert to lowercase. it would be possible to maintain letter case if we saved the original
    # input and then re-split it at the very end of this method, if that's desirable

    if verbose:
        logging.debug("syllabifying word: " + inp)

    if len(inp) <= 1:
        return inp
    if inp.lower() == "euouae":
        return "e-u-o-u-ae".split("-")
    if inp.lower() == "cuius":
        return "cu-ius".split("-")
    if inp.lower() == "eius":
        return "e-ius".split("-")
    if inp.lower() == "iugum":
        return "iu-gum".split("-")
    if inp.lower() == "iustum":
        return "iu-stum".split("-")
    if inp.lower() == "iusticiam":
        return "iu-sti-ci-am".split("-")
    if inp.lower() == "iohannes":
        return "io-han-nes".split("-")
    word = [inp]

    # for each unbreakable unit (consonant_groups and dipthongs)
    for unit in consonant_groups + diphthongs:
        new_word = []

        # check each segment of the word for this unit
        for segment in word:
            # if this segment is marked as unbreakable or does not have the unit we care about,
            # just add the segment back into new_word and continue
            if "*" in segment or unit not in segment:
                new_word.append(segment)
                continue

            # otherwise, we have to split this segment and then interleave the unit with the rest
            # this 'reconstructs' the original word even in cases where the unit appears more than
            # once
            split = segment.split(unit)

            # necessary in case there exists more than one example of a unit
            rep_list = [unit + "*"] * len(split)
            interleaved = [val for pair in zip(split, rep_list) for val in pair]

            # remove blanks and chop off last extra entry caused by list comprehension
            interleaved = [x for x in interleaved[:-1] if len(x) > 0]
            new_word += interleaved
        word = list(new_word)

    # now split into individual characters anything remaining
    new_word = []
    for segment in word:
        if "*" in segment:
            new_word.append(segment.replace("*", ""))
            continue
        # if not an unbreakable segment, then separate it into characters
        new_word += list(segment)
    word = list(new_word)

    # add marker to units to mark vowels or diphthongs this time
    for i in range(len(word)):
        if word[i] in vowels + diphthongs:
            word[i] = word[i] + "*"

    if verbose:
        print("split list: {}".format(word))

    if not any(("*" in x) for x in word):
        return ["".join(word)]

    # begin merging units together until all units are marked with a *.
    escape_counter = 0
    while not all([("*" in x) for x in word]):
        # first stick consonants / consonant groups to syllables ahead of them
        new_word = []
        i = 0
        while i < len(word):
            if i + 1 >= len(word):
                new_word.append(word[i])
                break
            cur = word[i]
            proc = word[i + 1]
            if "*" in proc and "*" not in cur:
                new_word.append(cur + proc)
                i += 2
            else:
                new_word.append(cur)
                i += 1
        word = list(new_word)

        # then stick consonants / consonant groups to syllables behind them
        new_word = []
        i = 0
        while i < len(word):
            if i + 1 >= len(word):
                new_word.append(word[i])
                break
            cur = word[i]
            proc = word[i + 1]
            if "*" in cur and "*" not in proc:
                new_word.append(cur + proc)
                i += 2
            else:
                new_word.append(cur)
                i += 1
        word = list(new_word)

        if verbose:
            print("merging into syls:{}".format(word))

        escape_counter += 1
        if escape_counter > 100:
            raise RuntimeError(
                "input to syllabification script has created an infinite loop"
            )

    word = [x.replace("*", "") for x in new_word]

    return word


def syllabify_text(input, verbose=False):
    words = input.split(" ")
    word_syls = [syllabify_word(w, verbose) for w in words]
    # to keep consistency with the original Cantus,
    # a hyphen is added to every syllable before the last syllable in the word
    word_syls_hyphen = []
    for syl_list in word_syls:
        # this filters out the empty strings
        if syl_list:
            syl_list = [syl + "-" for syl in syl_list]
            syl_list[-1] = syl_list[-1].strip("-")
            word_syls_hyphen.append(syl_list)
    syls = [item for sublist in word_syls_hyphen for item in sublist]
    return syls


if __name__ == "__main__":
    inp = (
        "Quique terrigene et filii hominum simul in unum dives et pauper Ite "
        "Qui regis israel intende qui deducis velut ovem ioseph qui sedes super cherubin Nuncia "
        "Excita domine potentiam tuam et veni ut salvos facias nos Qui regnaturus "
        "Aspiciens "
        "Aspiciebam in visu noctis et ecce in nubibus celi "
        "filius hominis venit Et datum est ei regnum et honor et "
        "omnis populus tribus et lingue servient ei "
        "zxcvbnm zx cvbnmzxcv bnm "
        "aaaaa413aa a$a %aa"
    )
    res = syllabify_text(inp, True)
    print(res)