import os
from dotenv import load_dotenv

from langchain_neo4j import Neo4jVector
from langchain_ollama import OllamaEmbeddings

from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# https://python.langchain.com/docs/integrations/vectorstores/neo4jvector/
vector_store = Neo4jVector.from_existing_index(
    embedding=OllamaEmbeddings(
        base_url="http://localhost:11434", model="gemma2:latest"
    ),
    index_name="vector",
    url=os.getenv("NEO4J_URL"),
    username=os.getenv("NEO4J_USER"),
    password=os.getenv("NEO4J_PASS"),
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
    base_url="http://localhost:11434", model="llama3.2:latest", temperature=0
)

rag_chain = prompt | llm | StrOutputParser()


class RAGApplication:
    def __init__(self, retriever, rag_chain):
        self.retriever = retriever
        self.rag_chain = rag_chain

    def run(self, question):
        documents = self.retriever.invoke(question)
        doc_texts = "\\n".join([doc.page_content for doc in documents])
        answer = self.rag_chain.invoke([{"question": question, "documents": doc_texts}])
        return answer


rag_application = RAGApplication(retriever, rag_chain)
