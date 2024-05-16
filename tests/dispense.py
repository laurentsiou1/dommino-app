"test de quantités dispensées"

import dispense_data

print(dispense_data.absorbance_model_26_01_2024)

[A1,m1,lK1,A2,m2,lK2,pH0]=dispense_data.absorbance_model_26_01_2024

print(A1)

    
while(True):
    ph = input("ph courant : ")
    x=float(ph)
    print("current: ", x)
    delta = dispense_data.delta_pH(A1,m1,lK1,A2,m2,lK2,x,pH0,max_delta=0.6)
    target=x+delta
    print("valeur de pH visée : ", target)
    print("volume à ajouter : ", dispense_data.get_volume_to_dispense_uL(x,target))
