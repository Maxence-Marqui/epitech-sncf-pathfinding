def getID():
    with open('./store.txt', 'r') as file:
        lines = file.readlines()

    if lines:
        last_line = lines[-1].strip()

        elements = last_line.split(',')

        # Vérifier s'il y a au moins un élément après la division
        if elements:
            # Récupérer le premier élément avant la virgule
            premier_element = elements[0].strip()

            return premier_element
        else:
            return 1
    else:
        return 1