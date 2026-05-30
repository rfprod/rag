import os
from dotenv import load_dotenv

from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_qdrant import QdrantVectorStore
from langchain_ollama import OllamaEmbeddings

load_dotenv()

urls = ["https://github.com/rfprod/nx-ng-starter/blob/main/README.md"]
docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=250, chunk_overlap=0
)

doc_splits = text_splitter.split_documents(docs_list)

embedding = OllamaEmbeddings(base_url="http://localhost:11434", model="llama3.2:latest")

vector_store = QdrantVectorStore.from_documents(
    documents=doc_splits,
    embedding=embedding,
    collection_name="documents",
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    api_key=os.getenv("QDRANT__SERVICE__API_KEY", None),
)
