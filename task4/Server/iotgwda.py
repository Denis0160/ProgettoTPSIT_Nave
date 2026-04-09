import json # Modulo per la gestione dei file JSON
import socket # Modulo per la gestione delle socket di rete
import time # Gestione dei timestamp, dello sleep e dei timer
import threading
from xmlrpc import client # Gestione del server multithreading
import paho.mqtt.client as mqtt # Modulo per la gestione del protocollo MQTT
import cripto # Modulo per la gestione della crittografia

# Definizione della PATH del file di configurazione
CONFIG_FILE = "configurazione/parametri.conf"
# Definizione della PATH del file di output
OUTPUT_FILE = "iotp/db.json"




# Classe per gestire la media delle misurazioni dei vari sensori connessi al gateway
class SensorData:
    def __init__ (self, this_id: str, sensor_id: str, cabina: int, ponte: int): # Costruttore
        self.this_id = this_id # ID di questo gateway
        self.sensor_id = sensor_id # Stringa contenente l'ID del sensore che invia il dato
        # Posizione del sensore nella nave
        self.cabina = cabina
        self.ponte = ponte
        self.temp_sum = 0 # Somma delle temperature
        self.humidity_sum = 0 # Somma delle umidita'
        self.count = 0 # Numero di misurazioni effettuate
        self.send_count = 0 # Numero d'invio

    # Aggiunta di una nuova misura nella classe
    def add_measure(self, temp: float, hum: float):
        self.temp_sum += temp
        self.humidity_sum += hum
        self.count += 1

    # Reset della media delle misure, ritorna un dizionario JSON contenente l'output di tutte le misure
    def send_data(self):
        if self.count == 0:
            return None
        avg_temp = self.temp_sum / self.count
        avg_hum = self.humidity_sum / self.count
        self.send_count += 1
        self.temp_sum = 0
        self.humidity_sum = 0
        self.count = 0
        return {
            'invionumero': self.send_count,
            'cabina': self.cabina,
            'ponte': self.ponte,
            'temperaturam': avg_temp,
            'umiditam': avg_hum,
            'dataeora': time.time(),
            'identita': self.this_id
        }

# Dizionario dei sensori
sensor_data = {}
# Numero di rilevazioni inviate all'IoTPlatform
numero_rilevazioni_inviate = 0
# Crea una lista di socket per i client che vengono terminati a fine programma
client_sockets: dict[str, socket.socket] = {}
# Evento utilizzato per la terminazione di thread aggiuntivi
program_stop = threading.Event()

# Aggiunta di una nuova misura al sensore specificato, se non esiste viene creato
def add_measurement(sensor_id: str, this_id: str, cabina: int, ponte: int, temperature: float, humidity: float):
    if sensor_id not in sensor_data:
        sensor_data[sensor_id] = SensorData(this_id, sensor_id, cabina, ponte)
    sensor_data[sensor_id].add_measure(temperature, humidity)

# Fa un dump di tutti i parametri salvati di tutti i sensori in un json unico che viene ritornato come stringa
def send_all_data():
    output = []

    # Chiudi se non ci sono dati disponibili
    if not sensor_data:
        return None

    # Iterazione nei dati
    for sensor_id, sensor in sensor_data.items():
        data = sensor.send_data()
        if data is not None:
            output.append(data)

    # Dump in una stringa che viene poi ritornata
    return json.dumps(output)

# Funzione di apertura del socket server
def open_socket(IP: str, PORT: int):
    try:    
        # Creazione del socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Binding del socket all'indirizzo e porta specificati
        server_socket.bind((IP, PORT))
        # Messa in ascolto del socket su un massimo di 5 connessioni in coda
        server_socket.listen(5)
        return server_socket
    except OSError:
        print("Errore durante l'apertura del socket server")
        raise

# Funzione che viene eseguita in un thread separato per la
# gestione del singolo client in arrivo
def handle_client(name: str, parametri: dict, client_socket: socket.socket):
    print("Nuovo client: ", name)

    # Continua a ricevere dati finché la connessione è attiva
    while True:
        data = "" # Spazio di memoria per il salvataggio dei dati ricevuti
        # Ricezione dei dati inviati dal client
        try:
            while True: # Loop per ricevere tutti i chunk di dati
                chunk = client_socket.recv(1024)
                if not chunk:
                    if not data: # Se nessun dato e' stato letto, chiudi la connessione
                        raise ConnectionResetError
                    # Finito di leggere
                    break
                data += chunk.decode("utf-8")
                # Se viene trovato il limitatore di fine messaggio
                if "\n" in data:
                    # Rimuoverlo e uscire dal ciclo
                    data = data.split('\n')[0]
                    break
        except (ConnectionResetError, BrokenPipeError):
            break
        except KeyboardInterrupt:
            break
        except TimeoutError:
            continue
        except OSError:
            break

        # Stampa del json ricevuto
        # Conversione del dato in formato json
        print("Ricezione dati da ", name, ": ", data)
        try:
            data_json = json.loads(data)
        #Eccezione se il JSON è scritto male
        except json.JSONDecodeError as e:
            print("Errore sintassi JSON:", e)
            continue

        # Aggiunta della misura al sensore specifico
        add_measurement(data_json["identita"], parametri["IDENTITA_GIOT"], int(data_json["cabina"]), int(data_json["ponte"]), round(float(data_json["osservazione"]["temperatura"]), parametri["N_DECIMALI"]), round(float(data_json["osservazione"]["umidita"]), parametri["N_DECIMALI"]));

    # Se il loop viene chiuso, chiudere anche il socket
    print("Chiusura comunicazione con client ", name)
    client_socket.close()
    # Rimozione di questo socket client dal dizionario
    client_sockets.pop(name)

# Funzione eseguita in un thread separato per la gestione
# dell'invio dei parametri encriptati all'IoT platform
def platform_sender(parametri: dict, clientMqtt: mqtt.Client):
    # Variabile contenente l'orario dell'ultimo invio
    last_send = int(time.time() * 1000)

    # Continua l'esecuzione fino a quando l'evento di stop dei thread viene impostato
    while not program_stop.is_set():
        # Verifica del passaggio del tempo richiesto
        if int(time.time() * 1000) - last_send > 60_000 * parametri["TEMPO_INVIO"] :
            # Resetta il timer
            last_send = int(time.time() * 1000)

            # Salva una stringa contenente i parametri di output
            output_data = send_all_data()
            # Controlla se ci sono dati di output
            if output_data is None:
                continue
            # Stampa in output la stringa contenente i parametri per informare l'utente
            print("Invio parametri all'IoTPlatform: ", output_data)
            # Encripta l'output
            output_data_encrypted = cripto.criptazione(output_data)

            try: # Effettua l'invio
               clientMqtt.publish(parametri["TOPIC"], output_data_encrypted)
               time.sleep(1) # Attesa di un secondo per assicurarsi che il messaggio venga inviato

            except Exception as e:
                print("Errore durante l'invio ", e)
                continue

            # Incrementa la variabile globale del numero di rilevazioni che sono state inviate
            global numero_rilevazioni_inviate
            numero_rilevazioni_inviate += 1

# Metodo per avviare il server e gestire le connessioni in arrivo
# Questo metodo blocca il programma fino a interrupt CTRL+C
def start_server():
    # Lettura dei parametri dal file di configurazione
    try:
        with open(CONFIG_FILE, "r") as file:
            parametri = json.load(file)
    except Exception:
        print("Errore durante l'apertura del file di configurazione")
        raise

    clientMqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    clientMqtt.connect(parametri["BROKER"], parametri["PORTA_BROKER"], 60)

    # Apri il socket su porta ed ip specificati nei parametri
    server_socket = open_socket(parametri["IP_SERVER"], parametri["PORTA_SERVER"])
    # Impostare il timeout del socket in modo che blocchi per un secondo
    server_socket.settimeout(1.0)

    # Creazione del thread per l'invio dei dati all'IoT Platform
    platform_thread = threading.Thread(target=platform_sender, args=(parametri, clientMqtt))
    platform_thread.start()

    # Loop infinito per accettazione dei dati in arrivo dal client
    while True:
        try:
            # Accettazione della connessione in arrivo
            while True: # Loop per continuare a chiamare accept() finche' non esce con un timeout
                try:
                    client_socket, addr = server_socket.accept()
                except TimeoutError:
                    continue
                break

            # All'accettazione, invia il tempo di rilevazione al data collector
            client_socket.send(str(parametri["TEMPO_RILEVAZIONE"]).encode("utf-8"))
        except KeyboardInterrupt: # Termine programma
            program_stop.set() # Termina il thread dell'invio alla piattaforma
            terminate_all(client_sockets) # Termina i thread client
            # Stampa il numero di rilevazioni inviate
            global numero_rilevazioni_inviate
            print("Chiusura programma\nNumero di rilevazioni inviate all'IoTPlatform: ", numero_rilevazioni_inviate)
            return
        except Exception:
            print("Errore durante la connessione con il client.")
            continue

        # Viene dato un nome al thread che gestisce quel client, uguale
        # alla rappresentazione in stringa dell'indirizzo del client connesso.
        nome_handler = str(addr)
        # Aggiungere questo socket al dizionario dei socket
        client_sockets[nome_handler] = client_socket

        # Una volta stabilita la connessione con il client, avviare un nuovo thread per la gestione di questo
        # Passare al thread di gestione del client il socket e i parametri di configurazione
        client_thread = threading.Thread(target=handle_client, args=(nome_handler, parametri, client_socket))
        client_thread.start() # Avvio del thread client

# Passata una lista di socket, questa funzione chiama il shutdown di tutti questi
def terminate_all(socket_list: dict[str, socket.socket]):
    # Iterazione in tutti i socket client
    for name, sock in socket_list.items():
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass # Socket gia' chiuso

# Main programma
if __name__ == "__main__":
    start_server()