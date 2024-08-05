from spacy import *
import spacy

def prediction(txt):
    nlp = spacy.load("../model_2")
    detect_ville = []
    nl = spacy.load("fr_core_news_sm")
    test_text = txt.lower().replace("la gare de ", "").replace("gare de ", "").replace("la gare ", "").replace("gare ", "").replace("rendre", "")


    doc = nl(txt)
    localisation = []

    for ent in doc.ents:
        if ent.label_ == "LOC":  # Filtrez les entités qui sont des lieux
            localisation.append(ent.text.lower())

    ville = []
    for i in range(0, len(localisation)):
        ville.append(localisation[i].replace("la gare de ", "").replace("gare de ", "").replace("la gare ", "").replace("gare ", ""))

    doc = nlp(test_text.lower())

    if len(list(doc.ents)) == 2:
        for ent in doc.ents:
            for v in ville:
                if str(ent) in v:
                    detect_ville.append([ent.label_, ent.text])
#                     print("=>", ent.label_.lower(), ":", ent.text.upper())
    else:
        test_text = txt.lower().replace("la gare de ", "").replace("gare de ", "").replace("la gare ", "").replace("gare ", "").replace("rendre", "")
        doc = nlp(test_text.lower())

        for ent in doc.ents:
            for v in ville:
                if str(ent) in v:
                    detect_ville.append([ent.label_, ent.text])
#                     print("=>", ent.label_.lower(), ":", ent.text.upper())
                    
    return detect_ville