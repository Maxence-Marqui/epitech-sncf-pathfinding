import re
import random
import argparse

def read_all_lines(filename):
    file = open(filename, 'r', encoding='utf-8')
    lines = file.readlines()
    lines = [line.strip() for line in lines]
    file.close()
    return lines

sentences = read_all_lines("./sentences")
towns = read_all_lines("./towns")

parser = argparse.ArgumentParser(description='Display random trip, start and destination')
parser.add_argument('-n', '--number', help='Number of trip to print', default=10, type=int)
args = parser.parse_args()

for nb in range(args.number):
    sentence = random.choice(sentences)
    town_start = random.choice(towns)
    town_end = town_start
    while town_end == town_start:
        town_end = random.choice(towns)

    trip = sentence
    trip = re.sub(r'\bSTART\b', town_start, trip)
    trip = re.sub(r'\bEND\b', town_end, trip)
    print(trip)
