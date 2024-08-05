def storeSentence(id, sentence, code):
    with open('./store.txt', 'a', encoding='utf-8') as file:
        # Write content to the file
        file.write(f'{id}, {sentence}, {code}.\n')