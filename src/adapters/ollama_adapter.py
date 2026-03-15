from ollama import AsyncClient

class LLMAdapter:
    def __init__(self, client : AsyncClient, embed_model: str, chat_model:str):
        self.client = client
        self.embed_model = embed_model
        self.chat_model = chat_model
    async def generate_embeddings(self, text: str) -> list[float]:
        response = await self.client.embeddings(model=self.embed_model, prompt=text)
        return response.get('embedding', [])
    async def generate_answer(self, system_prompt: str, context: list[str], query: str) -> str:
        full_context = "\n\n".join(context)
        full_system_message = f"{system_prompt}\n\n--- DOCUMENT CONTEXT ---\n\n{full_context}"
        ollama_response = await self.client.chat(model = self.chat_model, messages=[
        {'role': 'system', 'content': full_system_message},
        {'role': 'user', 'content': query}
    ])
        return ollama_response['message']['content']