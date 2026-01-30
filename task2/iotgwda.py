import json; # Modulo per la gestione dei file JSON
import socket # Modulo per la gestione delle socket di rete
import time; # Gestione dei timestamp, dello sleep e dei timer
import cripto; # Modulo per la gestione della crittografia

# Definizione della PATH del file di configurazione
CONFIG_FILE = "parametri.conf"
# Definizione della PATH del file di output
OUTPUT_FILE = "iotdata.dbt"

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
            'identita': self.this_id,
            'dc': self.sensor_id
        }

# Dizionario dei sensori
sensor_data = {}

# Aggiunta di una nuova misura al sensore specificato, se non esiste viene creato
def add_measurement(sensor_id: str, this_id: str, cabina: int, ponte: int, temperature: float, humidity: float):
    if sensor_id not in sensor_data:
        sensor_data[sensor_id] = SensorData(this_id, sensor_id, cabina, ponte)
    sensor_data[sensor_id].add_measure(temperature, humidity)

# Fa un dump di tutti i parametri salvati di tutti i sensori in un json unico che viene ritornato come stringa
def send_all_data():
    output = []

    for sensor_id, sensor in sensor_data.items():
        data = sensor.send_data()
        if data is not None:
            output.append(data)

    return json.dumps(output)

# Funzione di apertura del socket server
def open_socket(IP: str, PORT: int):
    try:    
        # Creazione del socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Binding del socket all'indirizzo e porta specificati
        server_socket.bind((IP, PORT))
        # Messa in ascolto del socket su un massimo di 1 connessione in coda
        server_socket.listen(1)
        return server_socket
    except OSError:
        print("Errore durante l'apertura del socket server")
        raise

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

    # Apri il socket su porta ed ip specificati nei parametri
    server_socket = open_socket(parametri["IP_SERVER"], parametri["PORTA_SERVER"])

    # Loop infinito per accettazione dei dati in arrivo dal client
    while True:
        # Variabile contenente il tempo dell'ultimo invio
        last_send = 0

        try:
            # Accettazione della connessione in arrivo
            client_socket, addr = server_socket.accept()
            # All'accettazione, invia il tempo di rilevazione al data collector
            client_socket.send(str(parametri["TEMPO_RILEVAZIONE"]).encode())
        except KeyboardInterrupt:
            print("Chiusura programma")
            return
        except OSError:
            print("Errore durante l'handshake con il client")
            continue

        # Continua a ricevere dati finché la connessione è attiva
        while True:

            # Ricezione dei dati inviati dal client
            try:
                data = client_socket.recv(1024).decode()
                # Chiudi il loop se la connessione viene chiusa
                if not data:
                    break
            except KeyboardInterrupt:
                print("Chiusura programma")
                return
            except (ConnectionResetError, BrokenPipeError):
                break
            except TimeoutError:
                continue
            except OSError:
                print("Errore di comunicazione con il client")
                raise

            # Conversione del dato in formato json
            data_json = json.loads(data)

            # Aggiunta della misura al sensore specifico
            add_measurement(data_json["identita"], parametri["IDENTITA_GIOT"], int(data_json["cabina"]), int(data_json["ponte"]), float(data_json["osservazione"]["temperatura"]), float(data_json["osservazione"]["umidita"]));

            # Verifica del passaggio del tempo richiesto
            if int(time.time() * 1000) - last_send > 60_000 * parametri["TEMPO_INVIO"] :
                # Resetta il timer
                last_send = int(time.time() * 1000)

                # Salva una stringa contenente i parametri di output
                output_data = send_all_data()
                # Stampa in output la stringa contenente i parametri per informare l'utente
                print("Invio parametri all'IoTPlatform: ", output_data)
                # Encripta l'output
                output_data_encrypted = cripto.criptazione(output_data)

                try: # Effettua l'invio
                    # Stampa del json nel database (si simula un invio verso il server centrale)
                    with open(OUTPUT_FILE, "a") as db_file:
                        db_file.write(output_data_encrypted + "\n")
                except Exception as e:
                    print("Errore durante l'apertura del file di output: ", e)
                    continue
                

# Main programma
if __name__ == "__main__":
    start_server()