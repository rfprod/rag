import requests


from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_core.documents import Document

from langchain_qdrant import QdrantVectorStore
from langchain_ollama import OllamaEmbeddings

import skills as skills_module
import configuration as configuration_module


def load_markdown_urls(urls: list[str]) -> list[Document]:
    """Fetch raw Markdown from public URLs and wrap each one as a LangChain Document.

    Each URL is requested with a 30-second timeout. The response body becomes
    the document's ``page_content``, and the URL is stored in
    ``metadata["source"]`` so each document can be traced to its origin.

    URLs are fetched one at a time in the order given. The first failed request
    raises an exception, so no documents are returned for the remaining URLs.

    Args:
        urls: Public URLs that point to raw Markdown files, such as
            ``https://raw.githubusercontent.com/...`` links. Responses are
            stored as-is, so a URL that returns HTML rather than Markdown
            will produce a document containing HTML.

    Returns:
        One Document per URL, in the same order as ``urls``.

    Raises:
        requests.HTTPError: If any URL returns a 4xx or 5xx status code.
        requests.RequestException: If a request fails because of a connection
            error or a timeout.
    """
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


docs_list = []
for url, skill in skills_module.skill_urls.items():
    documents = load_markdown_urls([url])
    for doc in documents:
        doc.metadata["skill"] = skill
    docs_list.extend(documents)

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=250, chunk_overlap=0
)

doc_splits = text_splitter.split_documents(docs_list)

embedding = OllamaEmbeddings(
    base_url=configuration_module.OLLAMA_BASE_URL,
    model=configuration_module.OLLAMA_EMBEDDING_MODEL,
)

vector_store = QdrantVectorStore.from_documents(
    documents=doc_splits,
    embedding=embedding,
    force_recreate=True,
    collection_name=configuration_module.QDRANT_COLLECTION_NAME,
    url=configuration_module.QDRANT_URL,
    api_key=configuration_module.QDRANT_API_KEY,
)
