import os
from dotenv import load_dotenv

from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_neo4j import Neo4jVector
from langchain_ollama import OllamaEmbeddings

load_dotenv()

urls = ["https://github.com/rfprod/nx-ng-starter/blob/main/README.md"]
docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=250, chunk_overlap=0
)

doc_splits = text_splitter.split_documents(docs_list)
# https://python.langchain.com/docs/integrations/vectorstores/neo4jvector/
vector_store = Neo4jVector.from_documents(
    documents=doc_splits,
    embedding=OllamaEmbeddings(
        base_url="http://localhost:11434", model="llama3.2:latest"
    ),
    url=os.getenv("NEO4J_URL"),
    username=os.getenv("NEO4J_USER"),
    password=os.getenv("NEO4J_PASS"),
)
