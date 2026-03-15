import uuid
from src.adapters.qdrant_adapter import VectorStoreAdapter
from src.adapters.ollama_adapter import LLMAdapter

class RagService:
    def __init__(self, vector_store: VectorStoreAdapter, llm: LLMAdapter):
        self.vector_store = vector_store
        self.llm = llm

    async def chat_request(self, question: str, system_prompt:str, user_id: uuid.UUID) -> str:
        """Повний цикл RAG: Питання -> Вектор -> Контекст -> LLM"""
        
        question_vector = await self.llm.generate_embeddings(question)

        relevant_chunks = await self.vector_store.search_context(
            query_vector=question_vector, 
            user_id=user_id,
            limit=3
        )

        print(f"Found chunks: {len(relevant_chunks)}")
        for i, chunk in enumerate(relevant_chunks):
            print(f"Chunk {i}: {chunk[:50]}...")# Показуємо перші 50 символів
        if not relevant_chunks:
            print("DEBUG: No relevant chunks found for this user.")
            return "На жаль, у ваших документах немає інформації для відповіді на це питання."
        context_str = "\n---\n".join(relevant_chunks)

        prompt = (
            f"{system_prompt}\n\n"
            f"Using the following context, answer the user's question. "
            f"If there is no answer in the provided context, just say so.\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {question}"
        )

        response =  self.llm.generate_answer(query=question, context=prompt, system_prompt=system_prompt)
        return await response