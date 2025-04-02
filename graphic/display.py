"""Functions in link with display"""

def state2Text(state,type):
    if state==True: 
        if type=='dispenser':
<<<<<<< HEAD
            text='ON'
=======
            text='DISPENSE'
>>>>>>> test_francois
        elif type=='circuit entrance':
            text='WATER'
        elif type=='circuit exit':
            text='BIN'
    else:
        if type=='dispenser':
<<<<<<< HEAD
            text='OFF'
=======
            text='BOTTLE'
>>>>>>> test_francois
        elif type=='circuit entrance':
            text='IN'
        elif type=='circuit exit':
            text='OUT'
    return text