import json # Importa il modulo per gestire i file json esterni
import time #importa il modulo per gestire le pause (sleep)
import misurazione #importa il modulo che simula il sensore di temperatura


#funzione per caricare i parametri dal file di configurazione
def caricamento_parametri(fileName: str):
   
    try:
        with open(fileName) as json_file: #Apertura del file in modalità lettura
            data = json.load(json_file)  #Legge il file e salva i dati in una variabile utilizzabile nel programma
            
    #Eccezione se il file non esiste    
    except FileNotFoundError as e:
        print("Errore: file non trovato.", e)
    
    #Eccezione se il JSON è scritto male
    except json.JSONDecodeError as e:
        print("Errore sintassi JSON:", e)

    #Eseguito se non ci sono errori
    else:
        return data

    #Eseguito sempre
    finally:
        print("Operazione caricamento parametri terminata")
        

rilevazioni = 1 #Variabile globale per ID progressivo delle rilevazioni

#Classe che rappresenta un DatoIoT
class DatoIoT:
    
    #costruttore della classe DatoIoT
    def __init__(self, temperatura: float, umidita: float, cabina: int, ponte: int):
        
        global rilevazioni #Uso della variabile globale per ID rilevazione

        # Inizializzazione attributi
        self.temperatura = temperatura
        self.umidita = umidita
        self.cabina = cabina
        self.ponte = ponte
        self.dataeora = time.time() #salva data e ora corrente
        self.rilevazione = rilevazioni 

        #Incremento ID rilevazione
        rilevazioni += 1

    #Metodo per convertire l'oggetto in formato JSON
    def to_json(self):
        return json.dumps(self.__dict__)

#Funzione principale di simulazione IoT
def simulazione_iot():
    try:
        parametri = caricamento_parametri('parametri.conf') #Caricamento parametri

        #Loop infinito lettura
        while True:
            try:
                temperatura = misurazione.on_temperatura(parametri["N_DECIMALI"])  #Lettura temperatura
                umidita = misurazione.on_umidita(parametri["N_DECIMALI"]) #Lettura umidità
                dato = DatoIoT(temperatura, umidita, parametri["CABINA"], parametri["PONTE"]) #Creazione oggetto dato IoT

                print(dato.to_json())#Stampa JSON

                #Scrittura su file
                with open('iotdata.dbt', "a") as file_output:
                    file_output.write(dato.to_json() + "\n")

            #Errore nella lettura o scrittura file
            except IOError as e:
                print("Errore nella lettura o scrittura file:", e)

            #Altri errori generici
            except Exception as e:
                print("Errore generico:", e)

            #Attesa
            time.sleep(parametri["TEMPO_RILEVAZIONE"])

    #Gestione CTRL+C
    except KeyboardInterrupt:
        print("\nTerminazione del programma")

    #Eseguito sempre
    finally:
        print("Programma terminato correttamente")


#Main programma
if __name__ == "__main__":
    simulazione_iot()