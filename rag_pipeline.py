import json
import os
from openai import OpenAI
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import logging
from app.config import get_settings
import uuid
from rag_utils import get_embedding, search_similar_tickets

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Initialize OpenAI client
try:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    raise

# Milvus connection settings
COLLECTION_NAME = 'tickets'

def connect_to_milvus():
    try:
        connections.connect(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            user=settings.MILVUS_USER,
            password=settings.MILVUS_PASSWORD
        )
        logger.info("Successfully connected to Milvus")
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
        raise

def create_collection():
    try:
        # Check if collection exists
        if utility.has_collection(COLLECTION_NAME):
            logger.info(f"Collection {COLLECTION_NAME} already exists")
            return Collection(COLLECTION_NAME)

        # Define collection schema
        fields = [
            FieldSchema(name='id', dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name='ticket_id', dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name='machine_model', dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name='serial_number', dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name='issue_description', dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name='affected_components', dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name='customer', dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name='reported_date', dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name='priority', dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name='status', dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name='resolution_solution', dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name='root_cause', dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name='resolution_date', dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name='technician', dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, dim=1536)
        ]
        schema = CollectionSchema(fields=fields, description='Ticket data for RAG')
        collection = Collection(name=COLLECTION_NAME, schema=schema)
        
        # Create index on the embedding field
        index_params = {
            'metric_type': 'L2',
            'index_type': 'IVF_FLAT',
            'params': {'nlist': 1024}
        }
        collection.create_index(field_name='embedding', index_params=index_params)
        logger.info(f"Created collection {COLLECTION_NAME} with index")
        return collection
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        raise

# Load ticket data
def load_tickets(file_path):
    try:
        with open(file_path, 'r') as f:
            tickets = json.load(f)
            logger.info(f"Successfully loaded {len(tickets)} tickets from {file_path}")
            return tickets
    except Exception as e:
        logger.error(f"Failed to load tickets: {e}")
        raise

# Ingest data into Milvus
def ingest_tickets(tickets, collection):
    try:
        entities = []
        for ticket in tickets:
            # Create a text chunk from issue description and resolution
            text_chunk = f'Issue: {ticket["issue_description"]}\nResolution: {ticket["resolution_solution"]}'
            embedding = get_embedding(text_chunk)
            entities.append({
                'id': str(uuid.uuid4()),
                'ticket_id': ticket['ticket_id'],
                'machine_model': ticket['machine_model'],
                'serial_number': ticket['serial_number'],
                'issue_description': ticket['issue_description'],
                'affected_components': json.dumps(ticket['affected_components']),
                'customer': ticket['customer'],
                'reported_date': ticket['reported_date'].isoformat(),
                'priority': ticket['priority'],
                'status': ticket['status'],
                'resolution_solution': ticket.get('resolution_solution', ''),
                'root_cause': ticket.get('root_cause', ''),
                'resolution_date': ticket.get('resolution_date', '').isoformat() if ticket.get('resolution_date') else '',
                'technician': ticket.get('technician', ''),
                'embedding': embedding
            })
        
        # Insert in batches to avoid memory issues
        batch_size = 100
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            collection.insert(batch)
            logger.info(f"Inserted batch {i//batch_size + 1}")
        
        collection.flush()
        logger.info(f"Successfully ingested {len(entities)} tickets")
    except Exception as e:
        logger.error(f"Failed to ingest tickets: {e}")
        raise

# Simple retrieval function
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

if __name__ == '__main__':
    try:
        # Connect to Milvus
        connect_to_milvus()
        
        # Create or get collection
        collection = create_collection()
        
        # Load and ingest tickets
        tickets = load_tickets('kb_samples/SupportTickets/testtickets.json')
        ingest_tickets(tickets, collection)
        
        # Example retrieval
        query = 'Machine displaying intermittent E-Stop errors'
        results = search_similar_tickets(query, collection)
        logger.info(f'Search results for query: {query}')
        for hits in results:
            for hit in hits:
                print(f'Ticket ID: {hit.entity.get("ticket_id")}')
                print(f'Machine Model: {hit.entity.get("machine_model")}')
                print(f'Serial Number: {hit.entity.get("serial_number")}')
                print(f'Issue Description: {hit.entity.get("issue_description")}')
                print(f'Affected Components: {hit.entity.get("affected_components")}')
                print(f'Customer: {hit.entity.get("customer")}')
                print(f'Reported Date: {hit.entity.get("reported_date")}')
                print(f'Priority: {hit.entity.get("priority")}')
                print(f'Status: {hit.entity.get("status")}')
                print(f'Resolution Solution: {hit.entity.get("resolution_solution")}')
                print(f'Root Cause: {hit.entity.get("root_cause")}')
                print(f'Resolution Date: {hit.entity.get("resolution_date")}')
                print(f'Technician: {hit.entity.get("technician")}')
                print(f'Distance: {hit.distance}')
                print('---')
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
    finally:
        # Clean up connections
        connections.disconnect(alias='default') 