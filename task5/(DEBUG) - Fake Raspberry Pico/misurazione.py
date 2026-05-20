import random
#
# Funzioni
#
def lettura_sensore():
    temp = random.uniform(-10, 50)
    hum = random.uniform(20, 80)

    return temp, hum
