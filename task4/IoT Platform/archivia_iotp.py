# Archiviazione dei dati provenienti dal publisher su file
import json # Gestione e decodifica del file json
import cripto # Decrittazione dei dati ricevuti dal Data Aggregator
import paho.mqtt.client as mqtt_client          #Libreria MQTT di Paho
import archivia_iotp   # Modulo per archiviare su file i dati provenienti dal publisher

# Funzione di callback per la connessione al broker MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print ("debug")
        print("Topic subscriber:",TOPIC,"- con QOS:", QOS)
        print("Connesso a MQTT Broker", BROKER_HOST,":",PORTA_BROKER)
        print()
        client.subscribe(TOPIC,QOS)
    else:
        print("Connessione fallita, return code %d\n", rc)
# Funzione di callback per la ricezione dei messaggi MQTT
def on_message(client, userdata, msg):
    # msg è una classe con membri topic, payload, qos, retain
    iot_data_criptato = msg.payload.decode("utf-8")
    iot_data = cripto.decriptazione(iot_data_criptato)
    # Stampa della stringa JSON ricevuta nell'archivio
    print("Dati ricevuti dal publisher:", iot_data)
    # Salvataggio dei dati su file
    salva_file(iot_data)
    
# Caricamento dei parametri dal file di configurazione con controllo errori
def carica_parametri() -> dict:
    try:
        with open("iotp.json", "r") as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print("File di configurazione non trovato.")
        raise
    except json.JSONDecodeError:
        print("Errore nella decodifica del file di configurazione.")
        raise
    
# Parametri di connessione con il broker MQTT
QOS = 0                                        # Qualità del servizio minima: nessuna garanzia consegna
KEEPALIVE = 60                                 # Intervallo massimo tra comunicazioni con broker

# Funzione di apertura del file di output
def apri_file(FILE, MODE):
    try:
        file = open(FILE, MODE)
        return file
    except IOError:
        print("Errore nell'apertura del file.")
        raise

def salva_file(iot_data):
    try:
        output_file.write(iot_data + "\n")  # Scrittura dei dati su file con newline
        output_file.flush()  # Assicurarsi che i dati vengano scritti su disco
    except IOError:
        print("Errore nella scrittura su file.")
        raise

# --------------------------------------------------------------------------
# Main
#
def __main__():
    # Caricamento dei parametri dal file di configurazione
    try:
        config = carica_parametri()
    except Exception as e:
        print("Errore nel caricamento dei parametri:", e)
        return
    # Le variabili di comunicazione con il broker MQTT e i parametri per l'archiviazione su file sono dichiarati globali per essere accessibili in tutte le funzioni
    global TOPIC, BROKER_HOST, PORTA_BROKER
    BROKER_HOST = config["broker"]["host"]
    PORTA_BROKER = config["broker"]["porta"]
    TOPIC = config["topic"]
    MODO = config["dbfile"]["modo"]
    FS = config["dbfile"]["file"]

    # Apertura del file per l'output
    try:
        global output_file
        output_file = apri_file(FS, MODO)
    except Exception as e:
        print("Errore nell'apertura del file di output:", e)
        return

    # Creazione del client MQTT e associazione delle funzioni di callback
    client = mqtt_client.Client()
    client.on_connect = on_connect    # Funzione definita on_connect associata al client in risposta alla connessione avvenuta
    client.on_message = on_message    # Funzione definita on_message associata al client per la gestione messaggio ricevuto
    client.connect(BROKER_HOST, PORTA_BROKER, KEEPALIVE)    # Connessione broker MQTT
    #
    try:
        client.loop_forever()  # Network loop con blocco infinito
    #
    except KeyboardInterrupt:
        print ("Stop subscriber")
        # Chiusura del file di output
        output_file.close()
    #

# Main
if __name__ == "__main__":
    __main__()