from openai import OpenAI
from typing import List
from app.config import get_settings

settings = get_settings()

class EmbeddingGenerator:
    def __init__(self):
        self.client = OpenAI()  # This will use the OPENAI_API_KEY environment variable automatically

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a given text using OpenAI's Ada model
        """
        response = self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts
        """
        response = self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=texts
        )
        return [item.embedding for item in response.data] 