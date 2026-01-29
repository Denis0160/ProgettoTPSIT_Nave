import json; # Modulo per la gestione dei file JSON
import socket; # Modulo per la gestione delle socket di rete
import cripto; # Modulo per la gestione della crittografia

# Definizione della PATH del file di configurazione
CONFIG_FILE = "parametri.conf"
# Definizione della PATH del file di output
OUTPUT_FILE = "iotdata.dbt"

# Funzione di apertura del socket server
def open_socket(IP: str, PORT: int):
    # Creazione del socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Binding del socket all'indirizzo e porta specificati
    server_socket.bind((IP, PORT))
    # Messa in ascolto del socket su un massimo di 1 connessione in coda
    server_socket.listen(1)
    return server_socket

# Metodo per avviare il server e gestire le connessioni in arrivo
# Questo metodo blocca il programma fino a interrupt CTRL+C
def start_server():
    # Lettura dei parametri dal file di configurazione
    with open(CONFIG_FILE, "r") as file:
        parametri = json.load(file)

    # Apri il socket su porta ed ip specificati nei parametri
    server_socket = open_socket(parametri["IP_SERVER"], parametri["PORTA_SERVER"])

    # Loop infinito per accettazione dei dati in arrivo dal client
    while True:
        # Accettazione della connessione in arrivo
        client_socket, addr = server_socket.accept()
        # All'accettazione, invia il tempo di rilevazione al data collector
        client_socket.send(str(parametri["TEMPO_RILEVAZIONE"]).encode())

        # Continua a ricevere dati finché la connessione è attiva
        while True:
            # Ricezione dei dati inviati dal client
            data = client_socket.recv(1024).decode()
            # Chiudi il loop se la connessione viene chiusa
            if not data:
                break
            # Decrittazione dei dati ricevuti
            data_decrypted = cripto.decriptazione(data)

            # Stampa dei dati ricevuti e decrittati nel file database
            with open(OUTPUT_FILE, "a") as db_file:
                db_file.write(data_decrypted + "\n")

# Main programma
if __name__ == "__main__":
    start_server()