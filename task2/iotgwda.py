import json; # Modulo per la gestione dei file JSON
import socket; # Modulo per la gestione delle socket di rete
import cripto; # Modulo per la gestione della crittografia

# Definizione della porta su cui il server ascolta
PORT = 6767

# Funzione di apertura del socket server
def open_socket():
    # Creazione del socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Binding del socket all'indirizzo e porta specificati
    server_socket.bind(("0.0.0.0", PORT))
    # Messa in ascolto del socket su un massimo di 1 connessione in coda
    server_socket.listen(1)
    return server_socket

# Metodo per avviare il server e gestire le connessioni in arrivo
# Questo metodo blocca il programma fino a interrupt CTRL+C
def start_server(server_socket):
    # Loop infinito per accettazione dei dati in arrivo dal client
    while True:
        # Accettazione della connessione in arrivo
        client_socket, addr = server_socket.accept()
        print(f"Connessione stabilita con {addr}")

        # Ricezione dei dati inviati dal client
        data = client_socket.recv(1024).decode()
        # Decrittazione dei dati ricevuti
        data_decrypted = cripto.decrittografa(data)
        print(f"Dati ricevuti: {data_decrypted}")