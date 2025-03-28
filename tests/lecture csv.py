"test de la lecture du fichier .csv"
from pathlib import Path
#import os

file = 'H:\A Nouvelle arbo\DOCUMENTS TECHNIQUES\Projets Collaboratifs\DOMMINO\CONCEPTION\V1\logiciel\sequence type 1.csv'

"""path = Path(__file__)
ROOT_DIR = path.parent.absolute()
app_default_settings = os.path.join(ROOT_DIR, "config/app_default_settings.ini")"""

def readSequenceInstructions():
    #file = self.sequence_config_file    #chaine de caracteres
    #print(file)
    import csv
    with open(str(file), newline='') as f:
        reader = csv.reader(f, delimiter=';')
        print("reader=",reader)
        instruction_table = []
        for l in reader:
            row = l[0:5]
            instruction_table.append(row)
            print(row)
    N=len(instruction_table)
    return instruction_table, N

def executeSequenceInstructions(table, N):
    for k in range(N):
        instruction = table[k]
        syringe = instruction[0]
        mode = instruction[1]
        value = instruction[2]
        pause = instruction[3]
        delay_mes = instruction[5]

        self.syringe_pump.dispense(syringe,str(mode),value)
        #self.wait for measure...

readSequenceInstructions()