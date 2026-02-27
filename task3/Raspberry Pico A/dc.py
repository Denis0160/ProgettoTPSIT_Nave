from logging import config
import misurazione #Importa il modulo che simula il sensore di temperatura/umidita
import time #importa il modulo per gestire le pause (sleep)
import json # Importa il modulo per gestire i file json esterni
import socket #Importa il modulo per fare le socket

from machine import Pin # Gestione GPIO per LED
import wifidc # Connessione e configurazione della rete wifi
import dht # Comunicazione con il sensore DHT11

DC_CONF = 'configurazionedc.json'
DA_ADDRESS = 'da.json'

#funzione per caricare i parametri dal file di configurazione
def caricamento_parametri(fileName: str) -> dict: # Ritorna un dizionario
    try:
        with open(fileName) as json_file: # Apertura del file in modalità di lettura
            data = json.load(json_file) #legge il file e salva i dati un un oggetto 
            return data
        
    #Eccezione se il file non esiste
    except FileNotFoundError as e:
        print("Errore: file non trovato.", e)
        raise
    #Eccezione se il JSON è scritto male
    except json.JSONDecodeError as e:
        print("Errore sintassi JSON:", e)
        raise
        
def main():
    try:
        config = caricamento_parametri(DC_CONF)
        da = caricamento_parametri(DA_ADDRESS)
        print("Caricamento parametri eseguito correttamente")
    except Exception as err:
        print("Errore durante il caricamento dei parametri: ", err)
        return
    
    internal_led = Pin(15, Pin.OUT) # Creazione dell'oggetto per la gestione del LED interno
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Crea la socket TCP
    sensore = dht.DHT11(Pin(config["cablaggio"]["segnale"]))
    
    try:
        client.connect((da["IP"], int(da["porta"]))) #conessione al DA (server)
        print("connesso al DA")
        
        tempo_rilevazione = int(client.recv(1024).decode())
        print(f"TEMPO_RILEVAZIONE ricevuto: {tempo_rilevazione} secondi")
        
        rilevazione = 0
        
        while True:
            try:
                temperatura, umidita = misurazione.lettura_sensore(sensore)
            except OSError as e:
                print("Errore durante la lettura dal sensore: ", e)
                continue
            
            rilevazione += 1

            # Integrazione della lettura nel dato iot
            dato_iot = config
            dato_iot.pop("cablaggio", None) # Rimozione della chiave "cablaggio" che e' inutile spedire
            dato_iot["osservazione"] = {} # Inizializzazione della chiave 'osservazione'
            dato_iot["osservazione"]["rilevazione"] = rilevazione
            dato_iot["osservazione"]["temperatura"] = temperatura
            dato_iot["osservazione"]["umidita"] = umidita

            # Conversione in JSON
            dato_json = json.dumps(dato_iot)
            
            internal_led.value(1) # Accendi il LED durante l'invio
            client.send((dato_json + '\n').encode()) #Invio del dato al DA, aggiungendo il limitatore di fine messaggio
            internal_led.value(0) # Spegni il LED
            
            print("Dato inviato al DA:")
            print(dato_json)
            
            time.sleep(tempo_rilevazione) #Attesa tra una rilevazione e l'altra
            
    except KeyboardInterrupt:
        print("Chiusura del client DC")
    except Exception as e:
        print("Errore generico:", e)
    finally:
        client.close()
        print("Client DC terminato correttamente")
    
    
if __name__ == "__main__":
    main()
    
    
            
            