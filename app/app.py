from tuya_connector import TuyaOpenAPI
import json
import subprocess
import time
import datetime
from pathlib import Path
from elasticsearch import Elasticsearch
import os
import logging
import yaml
import programDecode

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
DEVICE_TYPE = os.environ.get('DEVICE_TYPE')

logging.info(f"Miejsce to:{miejsce}")

# Utworzenie połączenia z Elasticsearch
try:
    es = Elasticsearch(es_host+":"+es_port, basic_auth=(es_username, es_password))
except Exception as e:
    logging.error(f"Błąd połączenia z Elasticsearch: {e}")

# Ścieżka do zapisu danych, gdy nie ma połączenia
offline_data_path = Path("offline_data_gniazdka.json")

file_path = 'list_device'
with open(file_path, 'r') as file:
    text_data = yaml.safe_load(file)
data = yaml.safe_load(text_data)
lista_id = data.get(DEVICE_TYPE)


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
    try:
        openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_KEY)
        openapi.connect()
    except Exception as e:
        logging.error(f"Błąd połączenia z Tuya API: {e}")
        continue
    for ind, DEVICE_ID in enumerate(lista_id):
        current_time = datetime.datetime.now()
        try:
            response = openapi.get(f'/v1.0/iot-03/devices/{DEVICE_ID}/status')
        except Exception as e:
            logging.error(f"Błąd podczas pobierania danych z Tuya API: {e}")
            continue
        if response.get('result') is None:
            logging.error("Odpowiedź z Tuya API jest niewłaściwa.")
            continue
        temp_set_man = None
        upper_temp = None
        mode = None

        for item in response['result']:
            if item['code'] == 'TempSet':
                temp_set_man = item['value'] * 0.5
            elif item['code'] == 'TempCurrent':
                upper_temp = item['value'] * 0.5
            elif item['code'] == 'Mode':
                mode = item['value']
            elif item['code'] == 'program':
                program = item['value']

        temp_set_program = programDecode.set_temperature(current_time, program)

        if mode == '1':
            temp_set = temp_set_man
        else:
            temp_set = temp_set_program

    # Tworzenie dokumentu do wysłania
        doc = {
            'timestamp': current_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'city': miejsce,
            'ustawiona_temp': temp_set,
            'biezaca_temp': upper_temp,
            'tryb': int(mode),
            'programowa_temp': temp_set_program,
            'manualna_temp': temp_set_man
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