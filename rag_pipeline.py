import json
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import os

KNOWLEDGE_BASE_PATH = "knowledge_base.json"
CHROMA_DB_DIR = "./chroma_db"

def initialize_vector_store():
    \"\"\"Initializes the vector store with documents from the knowledge base.\"\"\"
    # Load knowledge base
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        raise FileNotFoundError(f"{KNOWLEDGE_BASE_PATH} not found.")

    with open(KNOWLEDGE_BASE_PATH, 'r') as f:
        kb_data = json.load(f)

    documents = []
    
    # Process Pricing
    for plan_name, details in kb_data.get("pricing", {}).items():
        price = details.get("price")
        features = ", ".join(details.get("features", []))
        content = f"Plan: {plan_name}\nPrice: {price}\nFeatures: {features}"
        documents.append(Document(page_content=content, metadata={"source": "pricing", "plan": plan_name}))

    # Process Policies
    for policy_name, detail in kb_data.get("policies", {}).items():
        content = f"Policy ({policy_name}): {detail}"
        documents.append(Document(page_content=content, metadata={"source": "policy", "type": policy_name}))

    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(documents, embeddings, persist_directory=CHROMA_DB_DIR)
    return vectorstore

def get_retriever():
    \"\"\"Returns a retriever for the knowledge base.\"\"\"
    embeddings = OpenAIEmbeddings()
    # Check if DB already exists to avoid re-embedding on every run
    if os.path.exists(CHROMA_DB_DIR):
        vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
    else:
        vectorstore = initialize_vector_store()
    return vectorstore.as_retriever(search_kwargs={"k": 2})

def retrieve_knowledge(query: str) -> str:
    \"\"\"Retrieves relevant knowledge for a given query.\"\"\"
    retriever = get_retriever()
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant information found in the knowledge base."
    
    context = "\n\n".join([doc.page_content for doc in docs])
    return context
