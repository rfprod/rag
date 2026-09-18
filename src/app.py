import os
from dotenv import load_dotenv

import subprocess
import sys

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from langchain_ollama import OllamaEmbeddings

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

rag_application = None


class RAGApplication:
    def __init__(self, retriever, rag_chain):
        self.retriever = retriever
        self.rag_chain = rag_chain

    def run(self, question):
        documents = self.retriever.invoke(question)
        doc_texts = "\\n".join([doc.page_content for doc in documents])
        answer = self.rag_chain.invoke({"question": question, "documents": doc_texts})
        return answer


def initialize():
    """The initialization function must be called once during the application startup."""

    global rag_application

    qdrant_client = QdrantClient(
        url=os.getenv("QDRANT_URL", "https://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY", None),
    )

    try:
        qdrant_client.get_collection(collection_name="rag-app")
    except Exception as e:
        if isinstance(e, UnexpectedResponse) and getattr(e, "status_code", None) == 404:
            print("[i] Qdrant collection `rag-app` not found. Creating embeddings...")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            result = subprocess.run(
                [sys.executable, os.path.join(script_dir, "embeddings.py")],
                capture_output=True,
                text=True,
                cwd=script_dir,
            )
            print(result.stdout)
            if result.returncode != 0:
                print("[err] embeddings.py failed:")
                print(result.stderr)
                raise RuntimeError("embeddings.py failed during startup.")
            print("[i] Collection `rag-app` created. Continuing with startup...")
        else:
            raise

    embedding = OllamaEmbeddings(
        base_url="http://localhost:11434", model="embeddinggemma:latest"
    )

    vector_store = QdrantVectorStore(
        client=qdrant_client, collection_name="rag-app", embedding=embedding
    )
    retriever = vector_store.as_retriever(k=4)

    prompt = PromptTemplate(
        template="""You are an assistant for question-answering tasks.
      Use the following documents to answer the question.
      If you don't know the answer, just say that you don't know.
      Use three sentences maximum and keep the answer concise:
      Question: {question}
      Documents: {documents}
      Answer:
      """,
        input_variables=["question", "documents"],
    )

    llm = ChatOllama(
        base_url="http://localhost:11434", model="gemma3n:latest", temperature=0
    )

    rag_chain = prompt | llm | StrOutputParser()

    rag_application = RAGApplication(retriever, rag_chain)

    question = "What operating systems does nx-ng-starter support?"
    answer = rag_application.run(question)
    print("--- startup test ---")
    print("Question:", question)
    print("Answer:", answer.strip())
    print("--- startup test ---")
