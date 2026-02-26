# Simulazione
# Sensore di temperatura e umidità
#
# Script misurazione.py
# Parametro ingresso da main: N numero di decimali arrotondamento
#
# Simulazione sensore temperatura, da 10 a 40 gradi
# cifre decimali pari a N
#
import random   # Generazione numeri casuali
#
# Funzioni
#
def on_temperatura(min: int, max: int, errore: int):
    TEMP =(random.uniform(min,max)) + random.uniform(-errore,errore)
    TEMP = round(TEMP, 2)
    return TEMP
# Simulazione sensore umidità, da 20 a 90 gradi
# cifre decimali pari a N
def on_umidita(min: int, max: int, errore: int):
    UMID =(random.uniform(min,max)) + random.uniform(-errore,errore)
    UMID = round(UMID, 2)
    return UMID