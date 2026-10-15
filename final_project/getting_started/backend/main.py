from config import INDEX_NAME
from utils import get_es_client

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/regular_search")
async def search(search_query: str, skip: int = 0, limit: int = 10, year: str | None = None) -> dict:
    es = get_es_client(max_retries=1, sleep_time=5)
    response = es.search(
        index=INDEX_NAME,
        body={
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": search_query,
                                "fields": ["title", "explanation"]
                            }
                        }
                    ]
                }
            },
            "from": skip,
            "size": limit
        },
        filter_path=['hits.hits._source,hits.hits._score,hits.total'],
    )
    if year:
        hits = [hit for hit in response["hits"].get("hits", []) if hit["_source"].get("date", "").startswith(year)]
    else:
        hits = response["hits"].get("hits", [])
    total_hits = response["hits"]["total"]["value"]
    max_pages = (total_hits + limit - 1) // limit
    return {"hits": hits, "max_pages": max_pages}

@app.get("/api/v1/get_docs_per_year_count/")
async def get_docs_per_year_count(search_query: str) -> dict:
    es = get_es_client(max_retries=1, sleep_time=0)
    try:
        query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": search_query,
                            "fields": ["title", "explanation"]
                        }
                    }
                ]
            }
        }
        
        response = es.search(
            index=INDEX_NAME,
            body={
                "query": query,
                "aggs": {
                    "docs_per_year": {
                        "date_histogram": {
                            "field": "date",
                            "calendar_interval": "year",
                            "format": "yyyy"
                        }
                    }
                },
            },
            filter_path=['aggregations.docs_per_year']
        )
        return {"docs_per_year": extract_docs_per_year(response)}
    except Exception as e:
        return {"error": str(e)}

def extract_docs_per_year(response: dict) -> dict:
    aggregations = response.get("aggregations", {})
    docs_per_year_buckets = aggregations.get("docs_per_year", {})
    buckets = docs_per_year_buckets.get("buckets", [])
    return {bucket["key_as_string"]: bucket["doc_count"] for bucket in buckets}