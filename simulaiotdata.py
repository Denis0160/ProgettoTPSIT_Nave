# Importa il modulo per gestire i file json esterni
import json
# Per sleep()
import time
# Simulazione del sensore di temperatura
import misurazione

# Caricamento dei parametri
def caricamento_parametri(fileName: str):
    # Apertura file
    with open(fileName) as json_file:
        # Caricamento dati
        data = json.load(json_file)
        # Chiusura file
        json_file.close()
        # Ritorno dati
        return data

# ID rilevazione incrementale
rilevazioni = 1

# Classe DatoIoT
class DatoIoT:
    def __init__(self, temperatura: float, umidita: float, cabina: int, ponte: int):
        # Variabile globale rilevazione
        global rilevazioni

        self.temperatura = temperatura
        self.umidita = umidita
        self.cabina = cabina
        self.ponte = ponte
        self.dataeora = time.time()
        self.rilevazione = rilevazioni

        # Incremento ID rilevazione
        rilevazioni += 1

    def to_json(self):
        return json.dumps(self.__dict__)

# Loop infinito invio dati
def simulazione_iot():
    # Caricamento parametri
    parametri = caricamento_parametri('parametri.conf')

    # Loop infinito lettura
    while True:
        # Lettura temperatura e umidità
        temperatura = misurazione.on_temperatura(parametri["N_DECIMALI"])
        umidita = misurazione.on_umidita(parametri["N_DECIMALI"])
        # Creazione dato IoT
        dato = DatoIoT(temperatura, umidita, parametri["CABINA"], parametri["PONTE"])
        # Stampa dato IoT in formato JSON
        print(dato.to_json())
        
        # Stampa del dato all'interno del file
        with open('iotdata.dbt', "a") as file_output:
            file_output.write(dato.to_json() + "\n")
            file_output.close()

        
        # Attesa di tempo rilevazione
        time.sleep(parametri["TEMPO_RILEVAZIONE"])

# Main programma
if __name__ == "__main__":
    simulazione_iot()