from typing import List
import json
from utils import get_es_client
from elasticsearch import Elasticsearch
from config import INDEX_NAME, INDEX_NAME_N_GRAM
from tqdm import tqdm
from pprint import pprint

def index_data(documents: List[dict], use_n_gram: bool = False):
    es = get_es_client(max_retries=5, sleep_time=5)
    _ = _create_index(es, use_n_gram=use_n_gram)
    _ = _insert_documents(es=es, documents=documents, use_n_gram=use_n_gram)
    index_name = INDEX_NAME_N_GRAM if use_n_gram else INDEX_NAME
    pprint(f'Indexed {len(documents)} documents into index "{index_name}"')
    
    
def _create_index(es: Elasticsearch, use_n_gram: bool) -> dict:
    tokenizer = "n_gram_tokenizer" if use_n_gram else "standard"
    index_name = INDEX_NAME_N_GRAM if use_n_gram else INDEX_NAME
    es.indices.delete(index=index_name, ignore_unavailable=True)
    return es.indices.create(
        index=index_name,
        body={
            "settings": {
                "index": {
                    "max_ngram_diff": 29
                },
                "analysis": {
                    'analyzer': {
                        'default': {
                            'type': 'custom',
                            'tokenizer': tokenizer
                        }
                    },
                    'tokenizer': {
                        'n_gram_tokenizer': {
                            'type': 'ngram',
                            'min_gram': 1,
                            'max_gram': 30,
                            'token_chars': [
                                'letter',
                                'digit'
                            ]
                        }
                    }
                }
            }
        }
    )

def _insert_documents(es: Elasticsearch, documents: List[dict], use_n_gram: bool = False) -> dict:
    index_name = INDEX_NAME_N_GRAM if use_n_gram else INDEX_NAME
    operations = []
    for document in tqdm(documents, total=len(documents), desc="Indexing documents"):
        operations.append({'index': {'_index': index_name}})
        operations.append(document)
    return es.bulk(operations=operations)


if __name__ == "__main__":
    with open('../../../data/apod.json') as f:
        documents = json.load(f)
    index_data(documents=documents, use_n_gram=True) 