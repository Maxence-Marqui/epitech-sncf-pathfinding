from prediction import prediction
from langdetect import detect
import sys

def detect_language(text):
    try:
        language = detect(text)
        return language
    except:
        return None

def storeSentence(text):
    with open('./nlp_output.txt', 'a', encoding='utf-8') as file:
        # Write content to the file
        file.write(f'{text}\n')


def gen_output():
    res_lines = []

    with open(str(sys.argv[1]), 'r', encoding='utf-8') as file:
        for line in file:
            line = str(line.strip())
            elements = line.split(',')

            res = prediction(elements[1])

            if elements:
                number = elements[0].strip()
                if number.isdigit():
                    if len(res) == 2:
                        if detect_language(str(elements[1])) == 'fr':
                            if res[0][0] == 'DEPART':
                                depart = res[0][1]
                                arrivee = res[1][1]
                            else:
                                depart = res[1][1]
                                arrivee = res[0][1]

                            print(number + "," + depart + "," + arrivee)
                            res_lines.append((number + "," + depart + "," + arrivee))
                        else:
                            print(number + ",", "NOT_FRENCH")
                            res_lines.append((number + ",", "NOT_FRENCH"))
                    elif detect_language(str(elements[1])) != 'fr':
                        print(number + "," + "NOT_FRENCH" + ',')
                        res_lines.append((number + "," + "NOT_FRENCH" + ','))
                    else:
                        print(number + "," + "NOT_TRIP" + ',')
                        res_lines.append((number + "," + "NOT_TRIP" + ','))
                else:
                    print('0' + "," + "NOT_TRIP" + ',')
                    res_lines.append(('0' + "," + "NOT_TRIP" + ','))
    
    for line in res_lines:
        storeSentence(line)

if len(sys.argv) != 2:
    print("Usage: python script.py <argument>")
else:
    gen_output()