from typing import List, Dict, Any
from app.core.embeddings import EmbeddingGenerator
from app.database.milvus import MilvusClient
from openai import OpenAI
from app.config import get_settings

settings = get_settings()

class RAGEngine:
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.milvus_client = MilvusClient()
        self.client = OpenAI()  # This will use the OPENAI_API_KEY environment variable automatically

    def process_issue(self, issue_text: str) -> Dict[str, Any]:
        """
        Process a new issue and return relevant solutions
        """
        # Generate embedding for the issue
        embedding = self.embedding_generator.generate_embedding(issue_text)
        
        # Search for similar tickets
        similar_tickets = self.milvus_client.search_similar_tickets(embedding)
        
        # Generate response using OpenAI
        context = self._prepare_context(similar_tickets)
        response = self._generate_response(issue_text, context)
        
        return response

    def _prepare_context(self, similar_tickets: List[Dict[str, Any]]) -> str:
        """
        Prepare context from similar tickets
        """
        context = "Similar past issues and their solutions:\n\n"
        for ticket in similar_tickets:
            context += f"Issue: {ticket['issue_description']}\n"
            context += f"Solution: {ticket['resolution_solution']}\n"
            context += f"Root Cause: {ticket['root_cause']}\n\n"
        return context

    def _generate_response(self, issue_text: str, context: str) -> Dict[str, Any]:
        """
        Generate response using OpenAI
        """
        prompt = f"""
        You are a field service engineer assistant. Analyze the following issue and provide a solution based on similar past cases.

        Current Issue:
        {issue_text}

        {context}

        Please provide:
        1. A brief summary of the issue
        2. Suggested solution based on similar cases
        3. Confidence score (0-1)
        4. Reference to the most relevant past case
        """

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful field service engineer assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        # Parse the response
        content = response.choices[0].message.content
        lines = content.split('\n')
        
        return {
            "summary": lines[0].split(': ')[1] if len(lines) > 0 else "",
            "suggested_fix": lines[1].split(': ')[1] if len(lines) > 1 else "",
            "confidence": float(lines[2].split(': ')[1]) if len(lines) > 2 else 0.0,
            "source_case": lines[3].split(': ')[1] if len(lines) > 3 else ""
        } 