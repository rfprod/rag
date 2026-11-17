import os
import requests
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_core.documents import Document

from langchain_qdrant import QdrantVectorStore
from langchain_ollama import OllamaEmbeddings

load_dotenv()


def load_markdown_urls(urls: list[str]) -> list[Document]:
    """Fetch public raw Markdown URLs and return LangChain Documents."""
    docs = []

    for url in urls:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        docs.append(
            Document(
                page_content=response.text,
                metadata={"source": url},
            )
        )

    return docs


urls = [
    "https://raw.githubusercontent.com/rfprod/nx-ng-starter/refs/heads/main/README.md"
]
docs_list = load_markdown_urls(urls)
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=250, chunk_overlap=0
)

doc_splits = text_splitter.split_documents(docs_list)

embedding = OllamaEmbeddings(
    base_url="http://localhost:11434", model="embeddinggemma:latest"
)

vector_store = QdrantVectorStore.from_documents(
    documents=doc_splits,
    embedding=embedding,
    collection_name="rag-app",
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    api_key=os.getenv("QDRANT_API_KEY", None),
)
