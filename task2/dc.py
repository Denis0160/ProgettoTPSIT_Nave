from logging import config
import misurazione #Importa il modulo che simula il sensore di temperatura/umidita
import time #importa il modulo per gestire le pause (sleep)
import json # Importa il modulo per gestire i file json esterni
import socket #Importa il modulo per fare le socket

#funzione per caricare i parametri dal file di configurazione
def caricamento_parametri(fileName: str):
    
    try:
        with open(fileName) as json_file: # Apertura del file in modalità di lettura
            data = json.load(json_file) #legge il file e salva i dati un un oggetto 
            return data
        
    #Eccezione se il file non esiste
    except FileNotFoundError as e:
        print("Errore: file non trovato.", e)
        return None
    #Eccezione se il JSON è scritto male
    except json.JSONDecodeError as e:
        print("Errore sintassi JSON:", e)
        
    #Eseguito sempre
    finally:
        print("Operazione caricamento parametri terminata")
        


def main():
    parametri = caricamento_parametri('configurazionedc.conf') #Caricamento parametri

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Crea la socket TCP
    
    try:
        client.connect("127.0.0.1", 6767) #conessione al DA (server)
        print("connesso al DA")
        
        tempo_rilevazione = int(client.recv(1024).decode())
        print(f"TEMPO_RILEVAZIONE ricevuto: {tempo_rilevazione} secondi")
        
        rilevazione = 0
        
        while True:
            rilevazione +=1
            
            
            temperatura = misurazione.temperatura(
                config["sensore"]["tmin"],
                config["sensore"]["tmax"],
                config["sensore"]["erroret"]
            )

            umidita = misurazione.umidita(
                config["sensore"]["umin"],
                config["sensore"]["umax"],
                config["sensore"]["erroreu"]
            )

            # Creazione DatoIoT come da consegna
            dato_iot = {
                "cabina": config["cabina"],
                "ponte": config["ponte"],
                "sensore": config["sensore"],
                "identita": config["identita"],
                "osservazione": {
                    "rilevazione": rilevazione,
                    "temperatura": temperatura,
                    "umidita": umidita
                }
            }

            # Conversione in JSON
            dato_json = json.dumps(dato_iot)
            
            client.send(dato_json.encode()) #Invio del dato al DA
            
            print("Dato inviato al Da:")
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
    
    
            
            