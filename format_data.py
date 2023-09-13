"""Enregistrement des spectres de la séquence automatisée dans un fichier .csv au bon format
Ce programme crée des dossiers dans lesquels il crée des fichier .txt faits pour être
transformés en .csv avec excel et ensuite tourner sur matlab
A SIMPLIFIER
"""

import glob, os
import spectro.processing
from datetime import datetime

def directMeasureFile(set,folder):
    for 




#lambda
wl=[250,300,350,400,450,500,550,600,650]

#simulation d'un spectre en intensité
dark_ref = [25, 510, 232, 429, 823, 351, 453, 559, 620]
blanc_ref = [3122, 15066, 12372, 11399, 7383, 8327, 9898, 10432, 10100]
I1 = [2382, 12870, 7831, 8731, 5311, 7319, 8311, 8310, 8100]
I2 = [2280, 12190, 7280, 8011, 5209, 7279, 8290, 8280, 8049]
I3 = [2260, 12090, 7220, 7970, 5021, 6980, 7892, 8009, 7900]
pH=[4.8,6.5,8.2]
abs1 = processing.intensity2absorbance(I1,blanc_ref)
#print(abs1)
abs2 = processing.intensity2absorbance(I2,blanc_ref)
abs3 = processing.intensity2absorbance(I3,blanc_ref)

Absorbance_set = [abs1, abs2, abs3] #ça dépendra du nombre de valeurs de pH

N_lambda = len(blanc_ref);N_mes = len(pH)

#remplissage du fichier
output_string = "\t"
for j in range(N_mes-1):
    output_string += str(str(pH[j]))+'\t'
output_string += str(pH[N_mes-1])+'\n'    

for l in range(N_lambda): #chaque élément de la liste correspond à une ligne sur le .csv
    output_string += str(wl[l])+'\t'
    for j in range(N_mes-1):
        output_string += str(Absorbance_set[j][l])+'\t'
    output_string += str(Absorbance_set[N_mes-1][l])+'\n'

print(output_string)

set_params = "flowcell - spectro ST - C=5ppm - avec titreur POC blabla"
measure_folder = "H:/A Nouvelle arbo/DOCUMENTS TECHNIQUES/Projets Collaboratifs/DOMMINO/DONNEES DE MESURES"
experiment_description = "Tests de référence sur la flowcell exemple"
#C:/Users/francois.ollitrault/Desktop
#H:/A Nouvelle arbo/DOCUMENTS TECHNIQUES/Projets Collaboratifs/DOMMINO/DONNEES DE MESURES

dt=datetime.now()
date_string = dt.strftime('%Y-%m-%d')
experiment_folder=measure_folder+'/'+date_string+' - '+experiment_description

try:
    os.mkdir(experiment_folder)
except:
    print('Dossier existant')

datetime_string = dt.strftime('-%Y-%m-%d %H-%M-%S-')
output_name_csv = datetime_string+str(set_params)

f_out = open(experiment_folder+'/'+output_name_csv+'.txt','w') #création d'un fichier dans le répertoire
f_out.write(output_string)
f_out.close()