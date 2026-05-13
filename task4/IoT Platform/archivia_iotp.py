# Archiviazione dei dati e inoltro a ThingsBoard via MQTT
import json 
import cripto 
import paho.mqtt.client as mqtt_client          

# --- CONFIGURAZIONE THINGSBOARD (Aggiungi i tuoi dati qui) ---
# Se non hai un server locale, usa "demo.thingsboard.io"
TB_BROKER = "demo.thingsboard.io" 
TB_PORTA = 1883
TB_TOKEN = "IL_TUO_ACCESS_TOKEN_QUI" # <--- INSERISCI QUI IL TOKEN DEL DEVICE
TB_TOPIC = "v1/devices/me/telemetry"
# -----------------------------------------------------------

# Funzione di callback per la connessione al broker locale/aggregatore
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Connesso al Broker Locale {BROKER_HOST}. In ascolto su: {TOPIC}")
        client.subscribe(TOPIC, QOS)
    else:
        print(f"Connessione fallita, return code {reason_code}")

# Funzione di callback per la ricezione dei messaggi MQTT
def on_message(client, userdata, msg):
    try:
        # 1. Decodifica e Decrittazione
        iot_data_criptato = msg.payload.decode("utf-8")
        iot_data_chiaro = cripto.decriptazione(iot_data_criptato)
        
        print(f"Ricevuto e decriptato: {iot_data_chiaro}")

        # 2. Salvataggio su file locale (funzione originale)
        salva_file(iot_data_chiaro)
        
        # 3. Inoltro a ThingsBoard
        # ThingsBoard vuole un JSON. Se iot_data_chiaro è già stringa JSON, lo inviamo direttamente.
        tb_client.publish(TB_TOPIC, iot_data_chiaro, qos=1)
        print("Dato inoltrato correttamente a ThingsBoard.")
        
    except Exception as e:
        print(f"Errore durante l'elaborazione del messaggio: {e}")

def carica_parametri() -> dict:
    try:
        with open("iotp.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Errore caricamento iotp.json: {e}")
        raise

def apri_file(FILE, MODE):
    try:
        return open(FILE, MODE)
    except IOError:
        print("Errore nell'apertura del file.")
        raise

def salva_file(iot_data):
    try:
        output_file.write(iot_data + "\n")
        output_file.flush()
    except IOError:
        print("Errore nella scrittura su file.")

def __main__():
    try:
        config = carica_parametri()
    except: return

    global TOPIC, BROKER_HOST, PORTA_BROKER, output_file, tb_client
    BROKER_HOST = config["broker"]["host"]
    PORTA_BROKER = config["broker"]["porta"]
    TOPIC = config["topic"]
    
    # Apertura file locale
    output_file = apri_file(config["dbfile"]["file"], config["dbfile"]["modo"])

    # --- CLIENT 1: Connessione a ThingsBoard (Publisher) ---
    tb_client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    tb_client.username_pw_set(TB_TOKEN) # ThingsBoard usa il Token come username
    try:
        tb_client.connect(TB_BROKER, TB_PORTA, 60)
        tb_client.loop_start() # Avvia il loop in background per ThingsBoard
        print(f"Client ThingsBoard avviato (Broker: {TB_BROKER})")
    except Exception as e:
        print(f"Impossibile connettersi a ThingsBoard: {e}")
        return

    # --- CLIENT 2: Connessione al Broker Locale (Subscriber) ---
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    
    print(f"Connessione al broker locale...")
    client.connect(BROKER_HOST, PORTA_BROKER, 60)

    try:
        client.loop_forever() # Mantiene lo script attivo
    except KeyboardInterrupt:
        print("Chiusura in corso...")
        tb_client.loop_stop()
        output_file.close()

if __name__ == "__main__":
    __main__()
