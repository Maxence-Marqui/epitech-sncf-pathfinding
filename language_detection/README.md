# LANGUAGE DETECTION

## Introduction

This is my take on language detection

This program detects if a piece of text is written in French

## Usage

If <strong>french_model</strong> does not exist, launch :

`python create_model.py`

Then to start an interactive prompt, launch :

`python language_detection.py`

If you want to check if a string Is french, you can import the function

`is_french(sampletext, comparison_model, threshold=75)`

from the file <strong>language_detection.py</strong>, where :

- <strong>sampletext</strong> is the text to test

- <strong>comparison_model</strong> should be <strong>french_model</strong> open via pickle : `french_model = pickle.load(open('french_model', 'rb'))`

- <strong>threshold</strong> is a value between 0 and 1 indicating how well a text should perform against the <strong>french model</strong> to be considered french


## In depth explanation

This model takes into account the distribution of letters, by making probabilities on the number of occurrences of groups of letters in French texts.

Input dataset for french model creation : 

### N-grams

These groups of letters are called 'n-grams', form instant, "Hello world" split into trigrams (groups of three letters) gives the following result :

`['Hel', 'ell', 'llo', 'lo ', 'o w', ' wo', 'wor', 'orl', 'rld']`

### X-grams

N-grams works best if we combine trigrams with bigrams and individual letters<sup>[1](#1-n-gram-based-text-categorization)</sup>.

Hence, our x-grams function will output the following if given the same input string used earlier :

`['h', 'e', 'l', 'l', 'o', ' ', 'w', 'o', 'r', 'l', 'd', 'he', 'el', 'll', 'lo', 'o ', ' w', 'wo', 'or', 'rl', 'ld', 'hel', 'ell', 'llo', 'lo ', 'o w', ' wo', 'wor', 'orl', 'rld']`

Notice that we lowered characters, to cite How to do language detection<sup>[2](#2-how-to-do-language-detection---medium)</sup> :

"This will reduce the number of n-grams we get back, without losing much information about the language itself"

### Model creation

N-grams are grouped together to find their individual probabilities inside the sentence, thus creating a dictionary

This process is done again on the sentence we want to test

To get the probability for the input sentence to be french we apply a cosine function to our two dictionaries

The result is a value between 0 and 1, the threshold for a sentence to be considered french is set arbitrarily to 0.75

### Room for improvement

This method could be improved by the following manners :

Adding special characters such as '%' at the beginning and end of each word so that the probability of the position of the n-gram in the string is taken into account

Feed a French dictionary, and / or cities names

## Sources

### [1. N-Gram-Based Text Categorization](https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.21.3248&rep=rep1&type=pdf)

### [2. How to Do Language Detection - Medium](https://towardsdatascience.com/how-to-do-language-detection-using-python-nltk-and-some-easy-statistics-6cec9a02148)

### [3. Spracherkennung](https://textmining.wp.hs-hannover.de/Sprachbestimmung.html)

### [4. French Dataset](https://www.ortolang.fr/market/corpora/tcof)