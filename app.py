import streamlit as st
import json
from openai import OpenAI
from pymilvus import connections, Collection
from rag_utils import get_embedding, search_similar_tickets
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set page config
st.set_page_config(
    page_title="DiEngg",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state for chat history and context
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context" not in st.session_state:
    st.session_state.context = {}

# Connect to Milvus
def connect_to_milvus():
    try:
        connections.connect(
            host=os.getenv("MILVUS_HOST"),
            port=os.getenv("MILVUS_PORT"),
            user=os.getenv("MILVUS_USER"),
            password=os.getenv("MILVUS_PASSWORD")
        )
        return Collection("tickets")
    except Exception as e:
        st.error(f"Failed to connect to Milvus: {e}")
        return None

# Define the function schema for OpenAI function calling
function_schema = [
    {
        "name": "search_tickets",
        "description": "Search for relevant support tickets using RAG.",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_description": {"type": "string", "description": "Description of the issue."},
                "serial_number": {"type": "string", "description": "Serial number of the machine (optional)."}
            },
            "required": ["issue_description"]
        }
    }
]

def search_tickets(issue_description, serial_number=None):
    collection = connect_to_milvus()
    if not collection:
        return "Database connection error."
    query = issue_description
    if serial_number:
        query += f" Serial Number: {serial_number}"
    results = search_similar_tickets(query, collection, top_k=3)
    tickets = []
    for hits in results:
        for hit in hits:
            tickets.append({
                "ticket_id": hit.entity.get('ticket_id'),
                "machine_model": hit.entity.get('machine_model'),
                "issue_description": hit.entity.get('issue_description'),
                "resolution_solution": hit.entity.get('resolution_solution'),
                "root_cause": hit.entity.get('root_cause')
            })
    return tickets

# Main app
def main():
    st.title("🤖 DiEngg - Enginner for Engineer")
    st.write("Ask questions about support tickets and get relevant information from our knowledge base.")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare OpenAI chat history
        chat_history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        # Call OpenAI with function calling
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=chat_history,
            functions=function_schema,
            function_call="auto"
        )
        message = response.choices[0].message

        # If the model wants to call a function
        if message.function_call:
            func_name = message.function_call.name
            func_args = json.loads(message.function_call.arguments)
            if func_name == "search_tickets":
                tickets = search_tickets(**func_args)
                if isinstance(tickets, str):
                    reply = tickets
                elif tickets:
                    with st.chat_message("assistant"):
                        st.markdown("### 🗂️ Here are some relevant support tickets:")
                        for t in tickets:
                            with st.expander(f"📝 Ticket {t['ticket_id']} | {t['machine_model']}"):
                                st.markdown(f"**🆔 Ticket ID:** `{t['ticket_id']}`")
                                st.markdown(f"**🛠️ Machine Model:** `{t['machine_model']}`")
                                st.markdown(f"**❓ Issue Description:**\n{t['issue_description']}")
                                st.markdown(f"**✅ Resolution:**\n{t['resolution_solution']}")
                                st.markdown(f"**🔎 Root Cause:**\n{t['root_cause']}")
                    st.session_state.messages.append({"role": "assistant", "content": "[Ticket results above]"})
                else:
                    reply = "No relevant support tickets found. Please provide more details."
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    with st.chat_message("assistant"):
                        st.markdown(reply)
        else:
            # Otherwise, just reply with the model's message
            reply = message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)

if __name__ == "__main__":
    main() 