from pymilvus import connections, Collection, utility
from typing import List, Dict, Any
from app.config import get_settings
import json

settings = get_settings()

class MilvusClient:
    def __init__(self):
        self.connect()
        self.tickets_collection = None
        self.team_knowledge_collection = None
        self._setup_collections()
        self._ensure_indexes()

    def connect(self):
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            user=settings.MILVUS_USER,
            password=settings.MILVUS_PASSWORD
        )

    def _setup_collections(self):
        # Setup tickets collection
        if not utility.has_collection("tickets"):
            self._create_tickets_collection()
        self.tickets_collection = Collection("tickets")

        # Setup team knowledge collection
        if not utility.has_collection("team_knowledge"):
            self._create_team_knowledge_collection()
        self.team_knowledge_collection = Collection("team_knowledge")

    def _create_tickets_collection(self):
        from pymilvus import CollectionSchema, FieldSchema, DataType
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="ticket_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="machine_model", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="serial_number", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="issue_description", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="affected_components", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="customer", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="reported_date", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="priority", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="status", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="resolution_solution", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="root_cause", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="resolution_date", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="technician", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536)
        ]
        schema = CollectionSchema(fields=fields, description="Tickets collection")
        collection = Collection(name="tickets", schema=schema)
        
        # Create index on the embedding field
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)

    def _create_team_knowledge_collection(self):
        from pymilvus import CollectionSchema, FieldSchema, DataType
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="employee_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="role", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="skills", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="certifications", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="resolved_issues", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="experience_years", dtype=DataType.INT64),
            FieldSchema(name="region", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536)
        ]
        schema = CollectionSchema(fields=fields, description="Team knowledge collection")
        collection = Collection(name="team_knowledge", schema=schema)
        
        # Create index on the embedding field
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)

    def _ensure_indexes(self):
        """Ensure all collections have proper indexes"""
        # Ensure tickets collection index
        if self.tickets_collection:
            if not self.tickets_collection.has_index():
                index_params = {
                    "metric_type": "L2",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128}
                }
                self.tickets_collection.create_index(field_name="embedding", index_params=index_params)
            self.tickets_collection.load()

        # Ensure team knowledge collection index
        if self.team_knowledge_collection:
            if not self.team_knowledge_collection.has_index():
                index_params = {
                    "metric_type": "L2",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128}
                }
                self.team_knowledge_collection.create_index(field_name="embedding", index_params=index_params)
            self.team_knowledge_collection.load()

    def insert_ticket(self, ticket_data: Dict[str, Any], embedding: List[float]):
        self.tickets_collection.insert([
            [ticket_data["id"]],
            [ticket_data["ticket_id"]],
            [ticket_data["machine_model"]],
            [ticket_data["serial_number"]],
            [ticket_data["issue_description"]],
            [json.dumps(ticket_data["affected_components"])],
            [ticket_data["customer"]],
            [ticket_data["reported_date"].isoformat()],
            [ticket_data["priority"]],
            [ticket_data["status"]],
            [ticket_data.get("resolution_solution", "")],
            [ticket_data.get("root_cause", "")],
            [ticket_data.get("resolution_date", "").isoformat() if ticket_data.get("resolution_date") else ""],
            [ticket_data.get("technician", "")],
            [embedding]
        ])

    def search_similar_tickets(self, embedding: List[float], limit: int = 5):
        if not self.tickets_collection:
            raise Exception("Tickets collection not initialized")
            
        self.tickets_collection.load()
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }
        results = self.tickets_collection.search(
            data=[embedding],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            output_fields=["id", "ticket_id", "machine_model", "serial_number", "issue_description", 
                         "affected_components", "customer", "reported_date", "priority", "status",
                         "resolution_solution", "root_cause", "resolution_date", "technician"]
        )
        return results

    def insert_team_member(self, member_data: Dict[str, Any], embedding: List[float]):
        self.team_knowledge_collection.insert([
            [member_data["id"]],
            [member_data["employee_id"]],
            [member_data["name"]],
            [member_data["role"]],
            [json.dumps(member_data["skills"])],
            [json.dumps(member_data["certifications"])],
            [json.dumps(member_data["resolved_issues"])],
            [member_data["experience_years"]],
            [member_data["region"]],
            [embedding]
        ])

    def search_similar_team_members(self, embedding: List[float], limit: int = 5):
        self.team_knowledge_collection.load()
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }
        results = self.team_knowledge_collection.search(
            data=[embedding],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            output_fields=["id", "employee_id", "name", "role", "skills", "certifications", 
                         "resolved_issues", "experience_years", "region"]
        )
        
        # Parse JSON strings back to lists
        for hits in results:
            for hit in hits:
                entity = hit.entity
                if entity.get("skills"):
                    entity["skills"] = json.loads(entity["skills"])
                if entity.get("certifications"):
                    entity["certifications"] = json.loads(entity["certifications"])
                if entity.get("resolved_issues"):
                    entity["resolved_issues"] = json.loads(entity["resolved_issues"])
        
        return results

    def close(self):
        connections.disconnect("default") 