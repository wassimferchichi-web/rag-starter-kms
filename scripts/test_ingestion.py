import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.ingestion.loader import load_pdf
from src.ingestion.chunker import chunk_documents

docs = load_pdf('data/raw/test.pdf')
print(f'Pages chargees : {len(docs)}')

chunks = chunk_documents(docs)
print(f'Chunks generes : {len(chunks)}')
print(f'Chunk 0 : {chunks[0][chr(39)+"text"+chr(39)][:150]}')
print(f'Metadata : {chunks[0][chr(39)+"metadata"+chr(39)]}')
