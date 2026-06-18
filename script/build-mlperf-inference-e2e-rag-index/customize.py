from mlc import utils
import os


def preprocess(i):
    return {'return': 0}


def postprocess(i):
    env = i['env']

    cache_dir = os.getcwd()
    chunk_len = env.get('MLC_E2E_INGEST_CHUNK_LEN', '768')
    chunk_overlap = env.get('MLC_E2E_INGEST_CHUNK_OVERLAP', '32')
    db_name = f"vector_html_hnsw_len{chunk_len}_ov{chunk_overlap}_word"
    db_path = os.path.join(cache_dir, db_name + ".db")

    if not os.path.exists(db_path):
        return {'return': 1, 'error': f"Vector database not found after ingestion: {db_path}"}

    env['MLC_E2E_RAG_DATABASE'] = db_path
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = db_path

    return {'return': 0}
