#
# Creates & save model to detect if text is French
#

import collections
import math
import os
import pickle
import re

MODEL_FILE = 'french_model'
RESOURCES_FOLDER = "./tcof"


def ngram(string, n):
    res = []
    if n < len(string):
        for p in range(len(string) - n + 1):
            tg = string[p:p + n]
            res.append(tg)
    return res


def xgram(string):
    return [w for n in range(1, 4) for w in ngram(string.lower(), n)]


def get_top_10(dictionary):
    sorted_items = sorted(dictionary.items(), key=lambda x: x[1], reverse=True)
    return sorted_items[:10]


def buildmodel(text):
    # if ngram is only a space, ignore it
    model = collections.Counter(ng for ng in xgram(text) if ng != ' ')
    nr_of_ngs = sum(model.values())

    for w in model:
        model[w] = float(model[w]) / float(nr_of_ngs)

    return model


def cosinus(a, b):
    if not a or not b:
        return 0

    return sum([a[k] * b[k] for k in a if k in b]) / (
            math.sqrt(sum([a[k] ** 2 for k in a])) * math.sqrt(sum([b[k] ** 2 for k in b])))


def clean_str(raw_string):
    # remove all specials characters
    res = re.sub(r'[^a-zàâçéèêëîïôûùüÿñæœ\s\'\-]', '', raw_string.lower())

    # replace all line breaks & tabulations by spaces
    res = re.sub(r'[\s\r\n\-]', ' ', res)

    # remove consecutive spaces
    res = re.sub(' +', ' ', res)

    return res


def parse_trs_file(file):
    import xml.etree.ElementTree as ET

    tree = ET.parse(file)
    root = tree.getroot()

    sentence_array = [text.strip() for node in root.findall('.//Turn') for text in node.itertext() if text.strip()]
    concatenated_text = ' '.join(sentence_array)

    return clean_str(concatenated_text)


def concat_trs_files(resources_folder):
    res = ""

    for root, dirs, files in os.walk(resources_folder):
        for file in files:
            if file.endswith(".trs"):
                current_trs_file = os.path.join(root, file)
                res += parse_trs_file(current_trs_file)

    return res


if __name__ == '__main__':
    files_content = concat_trs_files(RESOURCES_FOLDER)
    french_model = buildmodel(files_content)

    pickle.dump(french_model, open(MODEL_FILE, 'wb'))
    print('model successfully written in file ' + MODEL_FILE)

    #print(get_top_10(french_model))
