# Connessione rete WiFi con Raspberry pico W
# Parametri WiFi recuperati da un file di configurazione
# in formato JSON (wifipico.conf)
#
# Script: picowifi.py
#
import rp2                    # Funzioni e classi specifiche per RP2040 - Raspberry Pi Pico
import network
import ubinascii              # Conversions between binary data and various encodings of it in ASCII form
import machine                # Funzioni relative all'HW utilizzato
import time
#
def Parametri_WiFi():
    import json
    with open('wifipico.conf', 'r') as file:
        credenziali = json.load(file)
        ssid = credenziali["ssid"]
        pasw = credenziali["pw"]
    return ssid,pasw
#
def Powersaving(scelta):
    """
    Per impostazione predefinita, il chip wireless attiva la modalità di risparmio energetico
    quando è inattivo, il che potrebbe renderlo meno reattivo.
    Se stai eseguendo un server o hai bisogno di maggiore reattività, 
    puoi modificare questa impostazione attivando la modalità di risparmio energetico.
    """
    if (scelta == "SI"):
        wlan.config(pm = 0xa11140)  # Disabilita powersaving mode
    else:
        pass 
    return
#
def Connessione_WiFi(time_out,s,p,pausa):
   """
   Connessione alla rete WiFi di nome s con password p,
   con un numero di tentativi pari a time_out e pausa
   pari a pausa con controllo stato ed errore diverso da 3
   Errori e significato:
   0  Link Down
   1  Link Join
   2  Link NoIp
   3  Link Up
   -1 Link Fail
   -2 Link NoNet
   -3 Link BadAuth
   """
   #
   wlan.connect(s,p)    # Connect to the specified wireless network --- wlan.disconnect()
   # Attessa connessione o fallimento
   print ("Tentativi (attesa): ", time_out)
   while time_out > 0:
       if wlan.status() < 0 or wlan.status() >= 3:
           break
       time_out = time_out - 1
       print("Tentativo connessione")
       time.sleep(pausa)
   # Gestione errore
   if wlan.status() != 3:
        while True:
            Errore_con_blink_led(wlan.status())
   else:
        print('Connessione riuscita')
        status = wlan.ifconfig()
        print(status)
        ip_assegnato = status[0]
        print("IP Pico: ", ip_assegnato)
   return
#
def Errore_con_blink_led(num_blinks):
    led = machine.Pin('LED', machine.Pin.OUT)
    for i in range(num_blinks):
        led.on()
        time.sleep(.2)
        led.off()
        time.sleep(.2)
    return
#
def Info_WiFi():
    """
    Visualizza parametri scheda WiFi
    #
    wlan.scan()
    Esegue la scansione delle reti wireless disponibili. Anche le reti nascoste,
    in cui l'SSID non viene trasmesso, verranno    scansionate se l'interfaccia WLAN lo consente.
    La scansione è possibile solo sull'interfaccia STA.
    Restituisce un elenco di tuple con le informazioni sui punti di accesso WiFi:
    (ssid, bssid, channel, RSSI, security, hidden)
    """
    mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()  # MAC chip wireless
    print('mac = ' + mac)
    print('Canale: ',wlan.config('channel'))
    print('SSID: ', wlan.config('essid'))
    print('Segnale: ', wlan.config('txpower'))
    print()
    print("Scansione")
    """
    There are five values for security:
        0 – open
        1 – WEP
        2 – WPA-PSK
        3 – WPA2-PSK
        4 – WPA/WPA2-PSK

    and two for hidden:
        0 – visible
        1 – hidden
    """
    print("(ssid, bssid, channel, RSSI, security, hidden)")
    """
    BSSID (Basic Service Set Identifier) serve a identificare inequivocabilmente in
    una rete Wi-Fi un punto di accesso Wi-Fi
    
    RSSI
    Misurazione della potenza del segnale: RSSI è una misura del livello di potenza del segnale Wi-Fi
    ricevuto sul ricevitore (ad esempio uno smartphone, un laptop o un altro dispositivo wireless).
    Scala decibel: RSSI è espresso in valori dBm negativi, dove un valore più alto (meno negativo)
    indica un segnale più forte
    """
    print (wlan.scan())
    print()
    return

# 
# Main
#
ATTESA = 10
TEMPO_PAUSA = 1
SSID,PASW = Parametri_WiFi()
#
# Configurazione connessione WiFi
#
rp2.country('IT')                    # Disponibili i canali wifi Italia per evitare possibili errori
wlan = network.WLAN(network.STA_IF)  # Interfaccia modalità stazione per connessione a un AP
wlan.active(True)                    # Attiva interfaccia WiFi
Powersaving('NO')                    # Abilitazione (NO) o disabilitazione (SI) powersaving mode
Connessione_WiFi(ATTESA,SSID,PASW,TEMPO_PAUSA)