import json
import os

file = open('data.json')
data = json.load(file)


dico = {}
for i in data['objects']:
    if ".ogg" in i:
        dico[i] = [data['objects'][i]["hash"], str(data['objects'][i]["hash"])[:2]]


for cle, valeur in dico.items():
    print("l'élément de clé", cle, "vaut", valeur)
