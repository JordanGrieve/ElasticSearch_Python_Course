import os
import time

from pprint import pprint
from elasticsearch import Elasticsearch

from dotenv import load_dotenv

load_dotenv()

def get_es_client(max_retries:int = 5, sleep_time:int = 5) -> Elasticsearch:
    i = 0
    while i < max_retries:
        try:
            es = Elasticsearch('http://localhost:9200', basic_auth=(os.getenv('ES_USERNAME'), os.getenv('ES_PASSWORD')))
            client_info = es.info()
            pprint("connected to Elasticsearch")
            pprint(f'Elasticsearch client info: {client_info}')
            return es
        except Exception as e:
            pprint(f'Error connecting to Elasticsearch: {e}')
            i += 1
            time.sleep(sleep_time)
    raise ConnectionError(f'Failed to connect to Elasticsearch after {max_retries} attempts')
