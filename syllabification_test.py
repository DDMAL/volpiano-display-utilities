from syllabized_full_texts import syllabized_full_texts
from cantus_text_syllabification import syllabify_text
import re

text_comparison = [["OldCantus", "New Syllabification"]]
print(len(syllabized_full_texts))
for i, chant_text in enumerate(syllabized_full_texts):
    chant_text = re.sub(r" \|(?=[^ ])", " | ", chant_text)
    chant_text = chant_text.replace("  "," ")
    chant_text = chant_text.strip()
    unsyllabified_text = chant_text.replace("-", "")
    try:
        syllabified_text = syllabify_text(unsyllabified_text, stringify_result=True)
        chant_text_words = chant_text.split(" ")
        syllabified_text_words = syllabified_text.split(" ")
        for old_cantus_word, utility_word in zip(chant_text_words, syllabified_text_words):
            if old_cantus_word == utility_word:
                continue
            text_comparison.append([old_cantus_word,
                            utility_word])
    except ValueError:
        continue

print(len(text_comparison))

import csv
with open("syllabification_comparison.csv", "w") as out_csv:
    csv_writer = csv.writer(out_csv)
    csv_writer.writerows(text_comparison)

