import os
from openai import OpenAI
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text):
    try:
        response = client.embeddings.create(
            model='text-embedding-ada-002',
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise

def search_similar_tickets(query_text, collection, top_k=3):
    try:
        query_embedding = get_embedding(query_text)
        search_params = {'metric_type': 'L2', 'params': {'nprobe': 10}}
        results = collection.search(
            data=[query_embedding],
            anns_field='embedding',
            param=search_params,
            limit=top_k,
            output_fields=['ticket_id', 'machine_model', 'serial_number', 'issue_description', 
                         'affected_components', 'customer', 'reported_date', 'priority', 'status',
                         'resolution_solution', 'root_cause', 'resolution_date', 'technician']
        )
        return results
    except Exception as e:
        logger.error(f"Failed to search similar tickets: {e}")
        raise 