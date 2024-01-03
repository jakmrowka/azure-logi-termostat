from tuya_connector import TuyaOpenAPI
import json
import subprocess
import time
import datetime
from pathlib import Path
from elasticsearch import Elasticsearch
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
ENDPOINT = "https://openapi.tuyaeu.com"

# Parametry konfiguracyjne
es_port = "9200"  # Port Elasticsearch

index_name = os.environ.get('ES_INDEX')
es_host = os.environ.get('ES_HOST')
miejsce = os.environ.get('MIEJSCE')
es_username = os.environ.get('ES_USERNAME')
es_password = os.environ.get('ES_PASSWORD')
ACCESS_ID = os.environ.get('TUYA_ACCESS_ID')
ACCESS_KEY = os.environ.get('TUYA_ACCESS_KEY')

logging.info(f"Miejsce to:{miejsce}")

# Utworzenie połączenia z Elasticsearch
es = Elasticsearch(es_host+":"+es_port, basic_auth=(es_username, es_password))

# Ścieżka do zapisu danych, gdy nie ma połączenia
offline_data_path = Path("offline_data_gniazdka.json")

lista_id = ["bf289bf7a00c812ce8mnvi"]

def save_offline_data(data):
    try:
        if offline_data_path.exists():
            with open(offline_data_path, "r+") as file:
                offline_data = json.load(file)
                offline_data.append(data)
                file.seek(0)
                json.dump(offline_data, file)
        else:
            with open(offline_data_path, "w") as file:
                json.dump([data], file)
    except Exception as e:
        logging.info(f"Błąd podczas zapisywania danych offline: {e}")

def send_data_to_es(doc):
    try:
        response = es.index(index=index_name, body=doc)
        logging.info(f"zapis to:{response}")
        if response.get('_shards', {}).get('successful', 0) > 0:
            return True
        else:
            logging.info("Wystąpił problem z zapisem danych do Elasticsearch.")
            return False
    except Exception as e:
        logging.info(f"Błąd podczas wysyłania danych do Elasticsearch: {e}")
        return False

while True:
    openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_KEY)
    openapi.connect()
    for ind, DEVICE_ID in enumerate(lista_id):
        current_time = datetime.datetime.now()
        response = openapi.get(f'/v1.0/iot-03/devices/{DEVICE_ID}/status')
        temp_set = None
        upper_temp = None

        for item in response['result']:
            if item['code'] == 'temp_set':
                temp_set = item['value']
            elif item['code'] == 'upper_temp':
                upper_temp = item['value']
    # Tworzenie dokumentu do wysłania
        doc = {
            'timestamp': current_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'city': miejsce,
            'ustawiona_temp': temp_set * 0.5,
            'biezaca_temp': upper_temp * 0.5
        }
        # logging.info(f"doc to:{doc}")
    # Próba wysłania danych
        if not send_data_to_es(doc):
            save_offline_data(doc)

    # Jeśli istnieją zapisane dane offline, spróbuj je wysłać
        if offline_data_path.exists():
            with open(offline_data_path, "r") as file:
                offline_data = json.load(file)

            if offline_data:
                succeeded = []
                for data in offline_data:
                    if send_data_to_es(data):
                        succeeded.append(data)

            # Usuwanie wysłanych danych
                offline_data = [d for d in offline_data if d not in succeeded]
                with open(offline_data_path, "w") as file:
                    json.dump(offline_data, file)

    # Czekanie 300 sekund
    time.sleep(300.0)