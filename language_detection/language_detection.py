#
# Determines if the input text is in French
#

import os.path
import pickle
import sys

from create_model import MODEL_FILE, buildmodel, cosinus, clean_str


def is_french(sampletext, comparison_model, threshold=75):
    sample_model = buildmodel(sampletext)
    frenchness_percentage = cosinus(comparison_model, sample_model) * 100
    print('frenchness : ' + str(frenchness_percentage) + '%')
    return frenchness_percentage > threshold


if __name__ == '__main__':
    while True:
        if not os.path.isfile(MODEL_FILE):
            print('model file ' + MODEL_FILE + ' not generated, please build model before retrying', file=sys.stderr)
            exit(1)

        french_model = pickle.load(open(MODEL_FILE, 'rb'))

        t = input("Enter text below, type 'exit' to quit :\n")
        if t == 'exit':
            exit(0)
        if is_french(clean_str(t), french_model):
            print('its french !')
        else:
            print('not french ...')