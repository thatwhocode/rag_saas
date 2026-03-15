from pymupdf import pymupdf
from adapters.qdrant_adapter import VectorStoreAdapter
from adapters.ollama_adapter import LLMAdapter
from uuid import UUID
class IngestionService():
    def __init__(self, qdrant_client : VectorStoreAdapter, ollama_client: LLMAdapter):
        self.qdrant_client = qdrant_client
        self.ollama_client = ollama_client

    def read_pdf(self, file_path: str) -> str:
        raw_data = ""
        with pymupdf.open(file_path) as doc:
            for page in doc:
                raw_data += page.get_text()    
        return raw_data
    def chunk_text(self, raw_data: str, chunk_size: int, overlap: int) -> list[str]:
        chunks = []
        step_size = chunk_size - overlap
        if not raw_data:
            return []

        for i in range(0, len(raw_data), step_size):
            end_index = i + chunk_size
            chunk = raw_data[i:end_index]
            if chunk.strip():
                chunks.append(chunk)
            
        return chunks
    
    async def process_and_save_document(self, file: str, user_id: UUID):
        text = self.read_pdf(file)
        chunks = self.chunk_text(text, 500, 50)
    
        vectors = []
        print(f"DEBUG: Починаю генерацію для {len(chunks)} чанків")

        for i, chunk in enumerate(chunks):
            vector = await self.ollama_client.generate_embeddings(chunk)
        
        # ПЕРЕВІРКА №1: Що прийшло від Ollama?
            print(f"DEBUG: Чанк {i} | Довжина вектора: {len(vector) if vector else 'NONE/EMPTY'}")
        
            if not vector or len(vector) == 0:
                print(f"⚠️ КРИТИЧНО: Ollama повернула порожній вектор для тексту: {chunk[:50]}...")
                continue
            
            vectors.append(vector)
    
        print(f"DEBUG: Всього зібрано векторів: {len(vectors)}")
    
        if len(vectors) > 0:
            await self.qdrant_client.save_chunks(chunks[:len(vectors)], vectors, user_id)
        else:
            print("❌ Жодного вектора не було згенеровано. Скасовую запит до Qdrant.")
